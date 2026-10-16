

https://github.com/user-attachments/assets/e3b45621-4262-4dcc-91b7-bb9189d1883a


# GR00T Crank Turning on a Unitree Humanoid

## Motivation

This project investigates the use of a humanoid robot to automate tedious manipulation of optical laboratory equipment. A related objective is to assess whether state-of-the-art robot-learning results can be reproduced in the laboratory and extended to new tasks, particularly cyclical manipulation.

The initial focus on small optical knobs shifted to crank turning after the knobs proved unsuitable for manipulation with the Dex3 hands. Crank turning serves as a proof of concept for rotational and cyclical tasks, with potential relevance to optical-equipment manipulation.

## Intended Approach

The planned pipeline using the GR00T vision-language-action (VLA) model consists of four stages:

1. Record teleoperated crank-turning demonstrations.
2. Convert the demonstrations to the data format required by GR00T.
3. Fine-tune the GR00T VLA model on the task.
4. Deploy the model on the robot and evaluate autonomous crank turning.

## Goals

1. Complete the GR00T fine-tuning pipeline on a new task to reproduce the published methodology and develop an understanding of the training and deployment process.
2. Design a benchmark for partial crank rotations informed by observed failure modes.
3. Publish completed datasets through the LeRobot community to support further research.

## Current Status

| Stage | Status |
| --- | --- |
| Crank test setup | A makeshift test bed was built; the proposed adjustable apparatus has not been built. |
| Wrist-camera mounts | Updated with rails to allow the cameras to be raised for a higher viewpoint. |
| Teleoperation and recording | Demonstration collection was attempted, but the recordings were not usable for training. |
| Crank manipulation | Partial turns were demonstrated while the Dex3 hands were not functioning. |
| Data conversion | Not performed. |
| GR00T fine-tuning | Not performed. |
| Autonomous inference | Not performed. |

Videos document partial crank-turning attempts at several crank orientations.

## Challenges and Outcomes

Non-functioning Dex3 hands and elbow singularities limited crank manipulation and prevented consistent collection of usable demonstrations. The elbow singularities are suspected to reflect an arm limitation independent of hand functionality. However, crank turning was not tested after the hands were repaired, so this interpretation remains unverified.

Additional issues included wrist-initialization failures, an incorrectly angled thumb joint, limited arm elevation, occasional unexpected arm motion, and a subsequent failure of the teleoperation code.

GR00T’s performance on crank turning has not yet been evaluated. Work to date has focused on task preparation, teleoperation, and identifying barriers to obtaining usable demonstrations.

## Documentation

- [Deployment notes](deployment_notes.md): Setup procedures, configuration details, and unresolved issues.
- [Project plan](project_plan.md): Objectives, proposed experiments, and research directions, distinguished from completed work.

## Future Research Directions

The following readings offer perspectives that may inform future development of the project:

- [Generalist GEN-1.5](https://generalistai.com/blog/gen-1.5): High-quality training data and in-context learning.
- [LeRobot robot folding](https://huggingface.co/spaces/lerobot/robot-folding): A deployment-focused example of learning a new robotic task.
- [Physical Intelligence π0.7](https://www.pi.website/blog/pi07): Skill composition.
- [TRI’s large behavior model work](https://toyotaresearchinstitute.github.io/lbm1/): Challenging manipulation tasks and data collection.



https://github.com/user-attachments/assets/9e6dbe43-99bc-440e-a9da-7a8f968b7087



https://github.com/user-attachments/assets/681f1c22-61a3-4d57-9e8e-fbe87988e326


