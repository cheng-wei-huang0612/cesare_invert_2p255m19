CC ?= cc

BUILD_DIR := build
ASM := invert25519_65a210bb6a4c.s
BENCH_BIN := $(BUILD_DIR)/bench
TEST_BIN := $(BUILD_DIR)/test
HAL_DIR := aarch64-bench/hal

CFLAGS ?= -O3
COMMON_CFLAGS := $(CFLAGS) -std=c11 -Wall -Wextra -Wpedantic -Werror
TESTS ?= 1000000
SEED ?= 0x25519
BENCH_CPU ?= 3

.PHONY: all bench test clean

all: $(BENCH_BIN) $(TEST_BIN)

bench: $(BENCH_BIN)
	@if ! command -v taskset >/dev/null 2>&1; then \
		echo "error: taskset is required for a pinned Pi 5 benchmark" >&2; \
		exit 1; \
	fi
	@taskset -c $(BENCH_CPU) $(BENCH_BIN)

test: $(TEST_BIN)
	@$(TEST_BIN) $(TESTS) $(SEED)

$(BUILD_DIR):
	@mkdir -p $@

$(BENCH_BIN): bench.c $(ASM) | $(BUILD_DIR)
	@if [ ! -f "$(HAL_DIR)/hal.c" ] || [ ! -f "$(HAL_DIR)/hal.h" ]; then \
		echo "error: aarch64-bench submodule is not initialized" >&2; \
		echo "run: git submodule update --init" >&2; \
		exit 1; \
	fi
	$(CC) $(COMMON_CFLAGS) -DPERF_CYCLES -I$(HAL_DIR) \
		bench.c $(HAL_DIR)/hal.c $(ASM) -o $@

$(TEST_BIN): test.c $(ASM) | $(BUILD_DIR)
	@if ! command -v pkg-config >/dev/null 2>&1 || ! pkg-config --exists gmp; then \
		echo "error: GMP development files are required for make test" >&2; \
		echo "on Raspberry Pi OS, run: sudo apt install libgmp-dev pkg-config" >&2; \
		exit 1; \
	fi
	$(CC) $(COMMON_CFLAGS) $$(pkg-config --cflags gmp) \
		test.c $(ASM) $$(pkg-config --libs gmp) -o $@

clean:
	$(RM) -r $(BUILD_DIR)
