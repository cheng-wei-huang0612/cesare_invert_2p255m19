CC ?= cc

TARGET ?= pi5
ASM_pi4 := invert25519_f8a6dea8cb0e.s
ASM_pi5 := invert25519_043d7a693cb3.s
ASM ?= $(ASM_$(TARGET))
ifeq ($(strip $(ASM)),)
$(error TARGET must be pi4 or pi5, or set ASM explicitly)
endif
# Separate binaries by implementation so switching TARGET cannot reuse old code.
BUILD_DIR ?= build/$(basename $(notdir $(ASM)))
BENCH_BIN := $(BUILD_DIR)/bench
TEST_BIN := $(BUILD_DIR)/test
ASM_STAMP := $(BUILD_DIR)/selected-asm
HAL_DIR := aarch64-bench/hal

CFLAGS ?= -O3
COMMON_CFLAGS := $(CFLAGS) -std=c11 -Wall -Wextra -Wpedantic -Werror
TESTS ?= 1000000
SEED ?= 0x25519
BENCH_CPU ?= 3

.PHONY: all bench test test-all verify-artifacts clean FORCE

all: $(BENCH_BIN) $(TEST_BIN)

bench: $(BENCH_BIN)
	@if ! command -v taskset >/dev/null 2>&1; then \
		echo "error: taskset is required for a pinned AArch64 benchmark" >&2; \
		exit 1; \
	fi
	@taskset -c $(BENCH_CPU) $(BENCH_BIN)

test: $(TEST_BIN)
	@$(TEST_BIN) $(TESTS) $(SEED)

test-all:
	@set -e; for variant in 65a210bb6a4c 043d7a693cb3 f8a6dea8cb0e; do \
		$(MAKE) test ASM=invert25519_$$variant.s BUILD_DIR=build/test-$$variant; \
	done

verify-artifacts:
	python3 scripts/verify_artifacts.py

$(BUILD_DIR):
	@mkdir -p $@

FORCE:

$(ASM_STAMP): FORCE | $(BUILD_DIR)
	@printf '%s\n' '$(abspath $(ASM))' > $@.tmp
	@if ! cmp -s $@.tmp $@; then mv $@.tmp $@; else $(RM) $@.tmp; fi

$(BENCH_BIN): bench.c $(ASM) $(ASM_STAMP) | $(BUILD_DIR)
	@if [ ! -f "$(HAL_DIR)/hal.c" ] || [ ! -f "$(HAL_DIR)/hal.h" ]; then \
		echo "error: aarch64-bench submodule is not initialized" >&2; \
		echo "run: git submodule update --init" >&2; \
		exit 1; \
	fi
	$(CC) $(COMMON_CFLAGS) -DPERF_CYCLES -I$(HAL_DIR) \
		bench.c $(HAL_DIR)/hal.c $(ASM) -o $@

$(TEST_BIN): test.c $(ASM) $(ASM_STAMP) | $(BUILD_DIR)
	@if ! command -v pkg-config >/dev/null 2>&1 || ! pkg-config --exists gmp; then \
		echo "error: GMP development files are required for make test" >&2; \
		echo "on Raspberry Pi OS, run: sudo apt install libgmp-dev pkg-config" >&2; \
		exit 1; \
	fi
	$(CC) $(COMMON_CFLAGS) $$(pkg-config --cflags gmp) \
		test.c $(ASM) $$(pkg-config --libs gmp) -o $@

clean:
	$(RM) -r $(BUILD_DIR)
