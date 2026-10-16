# GR00T Crank Turning on a Unitree Humanoid

## Motivation

This project explores using a humanoid robot to automate tedious manipulation of optical laboratory equipment. A related objective is to investigate whether state-of-the-art robot-learning models can be reproduced in the laboratory and adapted to new tasks, particularly cyclical manipulation.

The initial focus on small optical knobs shifted to crank turning after the knobs proved unsuitable for the Dex3 hands. Crank turning serves primarily as a proof of concept for rotational and cyclical tasks, with some connection to optical-equipment manipulation.

## Intended approach

The planned GR00T vision-language-action (VLA) pipeline is:

1. Record teleoperated crank-turning demonstrations.
2. Convert the demonstrations to the data format required by GR00T.
3. Fine-tune GR00T VLA on the task.
4. Deploy the model on the robot and evaluate autonomous crank turning.

## Goals:
1. Run through the entire Gr00t fine tuning pipline from start to finish on a new task to replicate paper and build intuition on how to train models
2. Design a partial cyclic benchmark based on my observations of failure modes.
3. Upload completed datasets into the Lerobot community for other researchers to build off of

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

Videos exists of the partial crank-turning attempt for various angles.

## Challenges and outcomes

Non-functioning Dex3 hands and elbow singularities limited crank manipulation and prevented consistent demonstration collection.  They are suspected to reflect an arm limitation independent of the hands. We were unable to try using the robot to turn the crank after the hands were fixed.

wrist-initialization failures, an incorrectly angled thumb joint, limited arm elevation, occasional unexpected arm motion, and a later teleoperation-code failure. 

The project has not yet evaluated GR00T's performance on crank turning. The work so far concerns task preparation, teleoperation, and the barriers to obtaining usable demonstrations.

## Documentation

- [Deployment notes](deployment_notes.md): recorded setup procedures, configuration details, and unresolved issues.
- [Project plan](project_plan.md): objectives, proposed experiments, and research directions, separated from completed work.

## Future Research directions

Some readings of interest that provide new directions for future projects: [Generalist GEN-1.5](https://generalistai.com/blog/gen-1.5) for high-quality data and in-context learning; [LeRobot robot folding](https://huggingface.co/spaces/lerobot/robot-folding) for deployment-focused task learning; [Physical Intelligence pi0.7](https://www.pi.website/blog/pi07) for skill composition; and [TRI's large behavior model work](https://toyotaresearchinstitute.github.io/lbm1/) for challenging tasks and data collection.


