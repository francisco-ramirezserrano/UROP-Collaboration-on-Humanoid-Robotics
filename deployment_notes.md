# Deployment and Teleoperation Notes

These notes reorganize the recorded setup procedures and troubleshooting observations. They are a record of the project, not a newly validated deployment procedure. The original notes mix robot 164 and robot 165 configurations; confirm which configuration applies before using a command.

## 1. Robot startup and network connection

The recorded startup sequence was:

1. Insert the battery and connect the robot to the router.
2. Go through zero-torque mode, damping mode, standing mode, and regular mode.
3. SSH into the robot.

Connecting the robot to the router by Ethernet resolved an observed CycloneDDS entity-discovery issue.

SSH sessions were reported to disconnect after approximately 15 minutes. Keeping the camera server running after a disconnect was an unresolved question.

## 2. Camera discovery and streaming

The notes identify a `teleimager` Conda environment; the original environment line also contains the unexplained text `cati`.

```bash
conda activate teleimager
teleimager-server --cf
```

The discovery command was used to find the cameras and copy their physical paths into the relevant `cam_config_*.yaml` configuration. The exact configuration filename was not recorded.

The project notes describe `start_teleimager.sh` as a script that dynamically finds the camera physical paths, avoiding repeated manual discovery:

```bash
./start_teleimager.sh
```

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

## 3. Quest connection and teleoperation

The notes specify connecting the Quest headset to the G1 router's Wi-Fi before starting the robot. The router password is located on its underside.

The recorded Quest browser address was:

```text
https://192.168.123.118:8012/?ws=wss://192.168.123.118:8012
```

The host IP must match the applicable network configuration. The recorded host interface was `enp6s0`, with address `192.168.123.118`.

Enter VR mode for hand tracking; joysticks were not required. The notes specify pressing `r` to begin following the operator's hand positions. The teleoperation environment was tentatively recorded as `tv`, but this was not confirmed.

`teleop_hand_and_arm.py` was modified to move the arms to the ready position even without an end-effector option, during a period when the Dex3 hands were not installed.

## 4. Recorded demonstration command

The following consolidates the options from the original notes into one multiline command. It has not been revalidated against the current script. Its 90-degree task description expresses the intended task, not an achieved outcome.

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

## 5. Hardware modifications

Wrist-camera mounts were updated with rails so the cameras could be moved upward for a higher viewpoint. Earlier notes identified insufficient mount sturdiness as an issue requiring iteration.

A makeshift crank test bed was built. It should not be confused with the proposed adjustable crank apparatus in [the project plan](project_plan.md).

Reference for teleoperation-related printed parts: [Unitree XR teleoperation device documentation](https://github.com/unitreerobotics/xr_teleoperate/blob/main/Device.md).

## 6. Observed problems and unresolved causes

| Observation | Status or interpretation |
| --- | --- |
| Dex3 hands not functioning during crank attempt | Video shows a partial turn under this condition |
| Elbow singularities during crank manipulation | Observed with non-functioning hands; suspected arm limitation independent of hands, not separately established |
| Wrists fail to initialize | Cause unresolved; lack of power was a possibility in the notes |
| One thumb joint angled incorrectly | Recorded hardware issue |
| Arms do not rise fully | Recorded motion limitation |
| Arms occasionally move up and down unexpectedly | Cause unresolved |
| Teleoperation code later stopped working | Failure recorded; cause unresolved |
| Turning in three main crank orientations was difficult | Reliable execution not achieved |
| SSH disconnects after about 15 minutes | Persistent server operation unresolved |

These issues prevented consistent usable demonstration collection. They do not establish GR00T model performance, which has not been evaluated on this task.
