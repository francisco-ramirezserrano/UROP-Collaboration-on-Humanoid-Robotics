# Deployment and Teleoperation Notes

This document summarizes the deployment configuration, teleoperation procedures, hardware modifications, and technical issues recorded during the project. The procedures have not been revalidated against the current system. The recorded configurations include both robot 164 and robot 165; the applicable robot and network configuration must therefore be confirmed before executing the commands.

## 1. Robot Startup and Network Connection

The recorded startup sequence was:

1. Transition through zero-torque mode, damping mode, standing mode, and regular mode.
2. Establish an SSH connection to the robot.

Connecting the robot to the router by Ethernet resolved an observed CycloneDDS entity-discovery issue.

SSH sessions were reported to disconnect after approximately 15 minutes. Maintaining a persistent SSH connection remains an unresolved operational requirement.

## 2. Camera Discovery and Streaming

Camera discovery and streaming used the `teleimager` Conda environment:

```bash
conda activate teleimager
teleimager-server --cf
```

The discovery command was used to identify the cameras. Their physical paths were then copied into the relevant `cam_config_*.yaml` configuration file. The exact configuration filename was not recorded.


The recorded server command was:

```bash
teleimager-server
```

Recorded WebRTC camera addresses:

| Address | Recorded association |
| --- | --- |
| `https://192.168.123.165:60001/` | Head camera |
| `https://192.168.123.165:60002/` | Other camera; wrist-side mapping not recorded |
| `https://192.168.123.165:60003/` | Other camera; wrist-side mapping not recorded |

Unplugging and reconnecting the head camera, or disconnecting all cameras, was noted as a troubleshooting action. On robot 164, the left wrist camera was connected to the left USB port and the right wrist camera to the right USB port.

## 3. Quest Connection and Teleoperation

The notes specify connecting the Quest headset to the G1 router's Wi-Fi before starting the robot. The router password is located on its underside.

The recorded Quest browser address was:

```text
https://192.168.123.118:8012/?ws=wss://192.168.123.118:8012
```

The host IP must match the applicable network configuration. The recorded host interface was `enp6s0`, with address `192.168.123.118`.

Teleoperation used VR mode with hand tracking; joysticks were not required. The recorded procedure specifies pressing `r` to initiate tracking of the operator's hand positions. The teleoperation environment was tentatively recorded as `tv`, but this was not confirmed.

`teleop_hand_and_arm.py` was modified to move the arms to the ready position even without an end-effector option, during a period when the Dex3 hands were not installed.

## 4. Recorded Demonstration Command

The command below consolidates the recorded demonstration-collection options. It has not been revalidated against the current script. The specified 90-degree rotation describes the intended task; successful execution of that rotation was not demonstrated.

```bash
python teleop_hand_and_arm.py \
  --input-mode hand \
  --display-mode immersive \
  --arm G1_29 \
  --ee dex3 \
  --img-server-ip 192.168.123.165 \
  --network-interface enp6s0 \
  --record \
  --task-dir "rotate_crank_v1" \
  --task-name "rotate crank" \
  --task-goal "rotate the crank 90 degrees." \
  --task-desc "Teleoperated Unitree G1_29 with Dex3 to rotate crank 90 degrees. Narrow-domain collection with fixed scene and consistent setup." \
  --task-steps "1. Start from home pose; 2. Reach to the crank; 3. Grasp the crank; 4. Rotate the crank; 5. Rotate until 90 degrees; 6. Release; 7. Retract."
```

Demonstration recording was started, but the resulting recordings were not usable for training. No data conversion, fine-tuning, or autonomous inference followed.

## 5. Hardware Modifications

Wrist-camera mounts were updated with rails so the cameras could be moved upward for a higher viewpoint. Earlier notes identified insufficient mount sturdiness as an issue requiring iteration.

A makeshift crank test bed was constructed to investigate the feasibility of crank manipulation. The proposed adjustable apparatus was not built.

Reference for teleoperation-related printed parts: [Unitree XR teleoperation device documentation](https://github.com/unitreerobotics/xr_teleoperate/blob/main/Device.md).

## 6. Observed Issues and Unresolved Causes

| Observation | Status or interpretation |
| --- | --- |
| Dex3 hands were not functioning during crank-turning attempts | Videos document partial turns at several crank orientations. Crank turning was not tested after the hands were repaired. |
| Elbow singularities during crank manipulation | Observed with non-functioning hands; suspected to reflect an arm limitation independent of hand functionality. This interpretation remains unverified. |
| Wrist-initialization failures | Cause unresolved; insufficient power was considered a possible explanation. |
| Incorrectly angled thumb joint | Recorded hardware issue. |
| Limited arm elevation | Recorded motion limitation. |
| Occasional unexpected vertical arm motion | Cause unresolved. |
| Subsequent teleoperation-code failure | Failure recorded; cause unresolved. |
| Difficulty turning the crank in three principal orientations | Reliable execution was not achieved. |
| SSH disconnections after approximately 15 minutes | Persistent server operation remains unresolved. |

These issues prevented consistent collection of usable demonstrations. Data conversion, GR00T fine-tuning, and autonomous inference have not been performed. The observations therefore characterize barriers to task preparation and data collection; they do not constitute an evaluation of GR00T performance.
