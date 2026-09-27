/* Copy this per function, e.g. wasm/src/calculate_damage.c
 * Compile flags must match the toolchain entry in targets/<game>/target.yaml
 * for whichever build produced the function you're matching. */
int example_function(int a, int b) {
    return a + b;
}
