#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

run_node_test <<'JS'
const rotation = requireFromRoot('shell/plugins/services/rotation/RotationModel.js')

assertEqual(JSON.stringify(rotation.parseSensorLine('=== Has accelerometer (orientation: bottom-up, tilt: tilted-down)')), '{"available":true,"orientation":"bottom-up"}', 'rotation reads the starting orientation')
assertEqual(JSON.stringify(rotation.parseSensorLine('    Accelerometer orientation changed: left-up')), '{"available":true,"orientation":"left-up"}', 'rotation reads orientation changes')
assertEqual(JSON.stringify(rotation.parseSensorLine('=== No accelerometer')), '{"available":false,"orientation":null}', 'rotation reports a missing accelerometer')
assertEqual(rotation.parseSensorLine('    Waiting for iio-sensor-proxy to appear'), null, 'rotation ignores unrelated monitor-sensor lines')
assertEqual(rotation.transformForOrientation('normal'), 0, 'rotation keeps normal upright')
assertEqual(rotation.transformForOrientation('left-up'), 1, 'rotation turns left-up by 90')
assertEqual(rotation.transformForOrientation('bottom-up'), 2, 'rotation flips bottom-up')
assertEqual(rotation.transformForOrientation('right-up'), 3, 'rotation turns right-up by 270')
assertEqual(rotation.transformForOrientation('undefined'), null, 'rotation holds position when lying flat')
assertEqual(rotation.transformForOrientation('bottom-up', 2), 0, 'rotation offset corrects an inverted sensor')
assertEqual(rotation.transformForOrientation('left-up', 2), 3, 'rotation offset wraps past 270')
assertEqual(rotation.transformForOrientation('normal', -1), 3, 'rotation offset accepts negative turns')
JS
