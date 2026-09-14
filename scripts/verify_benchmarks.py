#!/usr/bin/env python3
"""Offline verification of the published Pi 4 / Pi 5 paired measurements."""
from collections import defaultdict
from pathlib import Path
from statistics import median
import hashlib
import json
import math
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'benchmarks/20260914'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def same_number(a, b):
    return math.isclose(a, b, rel_tol=0, abs_tol=0.0000005)


def main():
    manifest = json.loads((EVIDENCE / 'manifest.json').read_text())
    for item in manifest['files']:
        require(sha((EVIDENCE / item['path']).read_bytes()) == item['sha256'], 'evidence hash mismatch: ' + item['path'])
    source_sets = []
    code_sets = []
    for host in manifest['hosts']:
        with zipfile.ZipFile(EVIDENCE / host['archive']) as z:
            hashes = json.loads(z.read('SHA256SUMS.json'))
            expected = set(z.namelist()) - {'SHA256SUMS.json', 'SHA256SUMS'}
            require(set(hashes) == expected, 'incomplete archive inventory')
            for name, digest in hashes.items():
                require(sha(z.read(name)) == digest, 'archive hash mismatch: ' + name)
            results = json.loads(z.read('results.json'))
            summary = json.loads(z.read('summary.json'))
            require(results['status'] == 'complete' and results['summary'] == summary, 'incomplete benchmark')
            require(results['benchmark_before']['model'] == host['model'], 'wrong target model')
            variants = set(results['variants'])
            require(len(variants) == 3 and len(results['tests']) == 3, 'wrong variant count')
            require(len(results['runs']) == 6 and len(results['controls']) == 2, 'incomplete repetitions')
            require({r['input_index'] for r in results['controls']} == {1, 2}, 'wrong controls')
            for name, digest in results['source_sha256'].items():
                require(sha(z.read('sources/' + name)) == digest, 'source snapshot mismatch')
                require(sha((ROOT / name).read_bytes()) == digest, 'published source differs from measured source: ' + name)
            source_sets.append(results['source_sha256'])
            texts = {}
            for test in results['tests']:
                variant = test['variant']
                require(test['returncode'] == 0 and test['inputs'] == 1008012 and test['assembly_calls'] == 2016028, 'native GMP checks incomplete')
                require(sha(z.read('validation/test-' + variant)) == test['binary_sha256'], 'test binary mismatch')
                text = z.read('objects/' + variant + '.text')
                require(text and text == z.read('objects/' + variant + '-bench.text'), 'objcopy changed code')
                require(sha(text) == test['text_sha256'], 'instruction hash mismatch')
                texts[variant] = sha(text)
            code_sets.append(texts)
            grouped = defaultdict(list)
            for run in results['runs'] + results['controls']:
                data = json.loads(z.read(run['measurement_file']))
                require(data['samples'] == 501 and data['batch'] == 1000, 'wrong measurement size')
                require(data['measurements'] == [dict(row, raw_batch_cycles=data['measurements'][i]['raw_batch_cycles']) for i, row in enumerate(run['measurements'])], 'run summary mismatch')
                rows = {row['name']: row for row in data['measurements']}
                require(set(rows) == variants | {'empty'}, 'missing measurements')
                empty = rows['empty']['raw_batch_cycles']
                baseline = rows['65a210bb6a4c']['raw_batch_cycles']
                for name, row in rows.items():
                    raw = row['raw_batch_cycles']
                    require(len(raw) == len(empty) == 501 and all(x > 0 for x in raw), 'invalid raw cycles')
                    net = sorted(a - b for a, b in zip(raw, empty))
                    ordered = sorted(raw)
                    delta = sorted(a - b for a, b in zip(raw, baseline))
                    for quantile, index in [('p10', 50), ('p50', 250), ('p90', 450)]:
                        require(same_number(net[index] / 1000, row['net_' + quantile]), 'incorrect paired quantile')
                        require(same_number(ordered[index] / 1000, row['raw_' + quantile]), 'incorrect raw quantile')
                    require(same_number(delta[250] / 1000, row['delta_baseline_p50']), 'incorrect paired difference')
                    if run['input_index'] == 0:
                        grouped[name].append(row)
            for name, rows in grouped.items():
                net = [row['net_p50'] for row in rows]
                saved = summary['results'][name]
                require(len(net) == 6 and net == saved['per_run_net_medians'], 'wrong repetitions')
                require(median(net) == saved['net_median'] and [min(net), max(net)] == saved['net_range'], 'incorrect aggregate')
            require(summary['ranking'] == sorted(variants, key=lambda v: summary['results'][v]['net_median']), 'incorrect ranking')
    require(source_sets[0] == source_sets[1], 'Pi 4/Pi 5 sources differ')
    require(code_sets[0] == code_sets[1], 'Pi 4/Pi 5 native implementation instructions differ')
    print('PASS: identical sources/code, six native GMP checks, both hosts, and all raw paired quantiles/medians.')


if __name__ == '__main__':
    main()
