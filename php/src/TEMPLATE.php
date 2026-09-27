<?php
// Copy this per function, e.g. php/src/calculate_damage.php
// Matching compares Zend opcodes (see docs/PHP_GUIDE.md), so this needs
// to run on the same PHP version the target was built for, but local
// variable names don't have to match.
function example_function($a, $b) {
    return $a + $b;
}
