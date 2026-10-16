# Crank-Turning Project Plan

## Motivation and Scope

This project investigates the use of a humanoid robot to automate tedious manipulation of optical laboratory equipment. A related objective is to assess whether state-of-the-art robot-learning results can be reproduced in the laboratory and extended to new tasks, particularly cyclical manipulation.

The initial focus on small optical knobs shifted to crank turning after the knobs proved unsuitable for manipulation with the Dex3 hands. Crank turning serves primarily as a proof of concept for rotational and cyclical tasks, with potential relevance to optical-equipment manipulation.

## Completed Work and Current Status

- Built a makeshift crank test bed.
- Updated wrist-camera mounts with rails for a higher viewpoint.
- Set up teleoperation and began recording demonstrations.
- Demonstrated partial crank turns while the Dex3 hands were not functioning; videos document attempts at several crank orientations.
- Documented setup procedures and hardware and software issues.

The recorded demonstrations were not usable for training. Data conversion, GR00T fine-tuning, and autonomous inference have not been performed. Crank turning was not tested after the Dex3 hands were repaired. 

## Project Objectives

1. Complete the GR00T fine-tuning pipeline on a new task to reproduce the published methodology and develop an understanding of the training and deployment process.
2. Design a benchmark for partial crank rotations informed by observed failure modes.
3. Publish completed datasets through the LeRobot community to support further research.

These objectives remain project goals; a benchmark and a completed dataset have not been produced.

## Intended Implementation Pipeline

1. Obtain a crank suitable for the Dex3 hands and establish working teleoperation.
2. Collect task demonstrations; the original target was 50 demonstrations.
3. Maintain consistent lighting, background, robot position, and task configuration, with smooth and repeatable teleoperation.
4. Convert recordings to the GR00T-compatible LeRobot format.
5. Fine-tune GR00T and record training statistics.
6. Run inference on the robot and evaluate crank turning and generalization.
7. Document the process and, if a usable dataset is produced, share it through GitHub or LeRobot.


## Proposed Adjustable Crank Apparatus

A concept for an adjustable crank apparatus was diagrammed but has not been constructed. The proposed adjustable parameters were:

- Turning radius.
- Handle thickness.
- Handle pitch relative to horizontal.
- Crank position in x and y.

Testing existing cranks was proposed to identify feasible handle dimensions and positions within the hand's workspace and the cameras' fields of view.

## Proposed Experiments and Evaluation Questions

The following experiments and evaluation methods have been proposed but not implemented:

- Categorize task failure modes and compare crank orientations.
- Investigate suitable training steps, epochs, and other fine-tuning parameters.
- Use an angle encoder to measure rotation and stop at a desired angle.
- Segment a recorded turn into examples corresponding to different angular displacements using encoder measurements.
- Explore image-based checks of whether the desired angle has been reached.

Open questions include how to specify clockwise and counterclockwise rotation, represent multiple revolutions, and distinguish progress through cycles when the initial and final images are visually similar.

## Research Directions

The following readings provide alternative perspectives on implementing the GR00T crank-turning project. The approaches have not been implemented in this system, and no approach has been selected for the next phase.

| Reading | Direction of Interest |
| --- | --- |
| [Generalist GEN-1.5](https://generalistai.com/blog/gen-1.5) | High-quality data and in-context learning |
| [LeRobot robot folding](https://huggingface.co/spaces/lerobot/robot-folding) | Deployment-focused task learning |
| [Physical Intelligence pi0.7](https://www.pi.website/blog/pi07) | Combining existing skills to perform a new skill |
| [TRI large behavior model](https://toyotaresearchinstitute.github.io/lbm1/) | Challenging laboratory tasks and factory data collection |

Additional reading included DreamZero and world action models, wearable data collection from Sunday Robotics and similar efforts, and AnySlot's use of generated goal images.

### Exploratory Implementation Proposals

The original notes proposed an AnySlot-inspired approach using a generated image of a desired crank position as a goal. They also proposed exploring a world action model that generates a trajectory while executing only the next action chunk. Both remain conceptual proposals and have not been implemented.

Other proposed directions include reward/advantage conditioning, SARM, and comparison with other open-source models. Their implementation and relevance to the current setup have not been fully investigated.

## Immediate Direction

Immediate next steps have not yet been determined. Further investigation of unresolved problems in the robotics pipeline is one possibility. Hardware observations, configuration details, and remaining uncertainties are documented in the [deployment notes](deployment_notes.md).
