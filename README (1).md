# GR00T Crank Turning on a Unitree Humanoid

## Motivation

This project explores using a humanoid robot to automate tedious manipulation of optical laboratory equipment. A related objective is to investigate whether state-of-the-art robot-learning models can be reproduced in the laboratory and adapted to new tasks, particularly cyclical manipulation.

The initial focus on small optical knobs shifted to crank turning after the knobs proved unsuitable for the Dex3 hands. Crank turning serves primarily as a proof of concept for rotational and cyclical tasks, with some connection to optical-equipment manipulation.

## Intended approach

The planned GR00T vision-language-action (VLA) pipeline is:

1. Record teleoperated crank-turning demonstrations.
2. Convert the demonstrations to the data format required by GR00T.
3. Fine-tune GR00T on the task.
4. Deploy the model on the robot and evaluate autonomous crank turning.

## Current status

| Stage | Status |
| --- | --- |
| Crank test setup | Makeshift test bed built; proposed adjustable apparatus not built |
| Wrist-camera mounts | Updated with rails to allow a higher camera viewpoint |
| Teleoperation and recording | Attempted; recordings were not usable for training |
| Crank manipulation | Partial turn demonstrated with non-functioning Dex3 hands |
| Data conversion | Not performed |
| GR00T fine-tuning | Not performed |
| Autonomous inference | Not performed |

A video exists of the partial crank-turning attempt. A video link has not yet been added to this documentation.

## Challenges and outcomes

Non-functioning Dex3 hands and elbow singularities limited crank manipulation and prevented consistent demonstration collection. The singularities were observed while the hands were not functioning. They are suspected to reflect an arm limitation independent of the hands, but that interpretation has not been separately established.

Additional notes record wrist-initialization failures, an incorrectly angled thumb joint, limited arm elevation, occasional unexpected arm motion, and a later teleoperation-code failure. Camera streaming, network configuration, and SSH disconnections also required troubleshooting.

The project has not yet evaluated GR00T's performance on crank turning. The work so far concerns task preparation, teleoperation, and the barriers to obtaining usable demonstrations.

## Documentation

- [Deployment notes](deployment_notes.md): recorded setup procedures, configuration details, and unresolved issues.
- [Project plan](project_plan.md): objectives, proposed experiments, and research directions, separated from completed work.

## Research directions

Readings provide alternative perspectives on implementing the project: [Generalist GEN-1.5](https://generalistai.com/blog/gen-1.5) for high-quality data and in-context learning; [LeRobot robot folding](https://huggingface.co/spaces/lerobot/robot-folding) for deployment-focused task learning; [Physical Intelligence pi0.7](https://www.pi.website/blog/pi07) for skill composition; and [TRI's large behavior model work](https://toyotaresearchinstitute.github.io/lbm1/) for challenging tasks and data collection.

These approaches have not been implemented here. Immediate next steps remain undecided.
