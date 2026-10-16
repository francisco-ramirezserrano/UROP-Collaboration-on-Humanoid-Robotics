# Crank-Turning Project Plan

## Motivation and scope

The project began with the goal of automating tedious turning of optical laboratory equipment. It also asks whether state-of-the-art robot-learning models can be reproduced locally and adapted to new tasks, especially cyclical manipulation.

Small knobs proved unsuitable for the Dex3 hands in the initial exploration. Crank turning became a proof of concept for rotational and cyclical tasks, with some connection to the original optical-equipment motivation.

## Completed work and current boundary

- Built a makeshift crank test bed.
- Updated wrist-camera mounts with rails for a higher viewpoint.
- Set up teleoperation and began recording demonstrations.
- Demonstrated a partial crank turn while the Dex3 hands were not functioning; a video exists.
- Recorded setup procedures and hardware/software problems.

The demonstrations were not usable for training. Data conversion, GR00T fine-tuning, and autonomous inference have not been performed. 

## Original intended pipeline

1. Obtain a crank suitable for the Dex3 hands and establish working teleoperation.
2. Collect task demonstrations; the original target was 50 demonstrations.
3. Keep lighting, background, robot position, and task setup consistent, with smooth and repeatable teleoperation.
4. Convert recordings to the GR00T-compatible LeRobot format.
5. Fine-tune GR00T and record training statistics.
6. Run inference on the robot and evaluate crank turning and generalization.
7. Document the process and, if a usable dataset is produced, share it through GitHub or LeRobot.


## Proposed adjustable crank apparatus

An adjustable apparatus was diagrammed but not built. Proposed variables included:

- Turning radius.
- Handle thickness.
- Handle pitch relative to horizontal.
- Crank position in x and y.

Testing existing cranks was proposed to identify feasible handle dimensions and positions given the hand's working space and camera view.

## Proposed experiments and evaluation questions

The following ideas remain unimplemented:

- Categorize task failure modes and compare crank orientations.
- Investigate suitable training steps, epochs, and other fine-tuning parameters.
- Use an angle encoder to measure rotation and stop at a desired angle.
- Segment a recorded turn into examples corresponding to different angular displacements using encoder measurements.
- Explore image-based checks of whether the desired angle has been reached.

Open task questions include clockwise versus counterclockwise turning, specifying multiple revolutions, and handling cycles in which the starting and ending images look similar.

## Research directions

These readings offer other perspectives on implementing the GR00T crank project. They have not been implemented here, and no approach has been selected as the next step.

| Reading | Interest stated for this project |
| --- | --- |
| [Generalist GEN-1.5](https://generalistai.com/blog/gen-1.5) | High-quality data and in-context learning |
| [LeRobot robot folding](https://huggingface.co/spaces/lerobot/robot-folding) | Deployment-focused task learning |
| [Physical Intelligence pi0.7](https://www.pi.website/blog/pi07) | Combining existing skills to perform a new skill |
| [TRI large behavior model](https://toyotaresearchinstitute.github.io/lbm1/) | Challenging laboratory tasks and factory data collection |

Other explored topics include DreamZero/world action models, wearable data collection from Sunday Robotics and similar efforts, and AnySlot's generated goal images.

### Earlier exploratory proposals

The original notes proposed an AnySlot-inspired approach using a generated image of a desired crank position as a goal. They also proposed exploring a world action model that generates a trajectory while executing only the next action chunk. Both remain conceptual proposals.

Other ideas in the notes include reward/advantage conditioning, SARM, and benchmarking other open-source models. Their implementation and relevance to the present setup have not been fully explored.

## Immediate direction

Immediate steps remain undecided. Investigating unresolved problems in the robotics pipeline is one possibility. The hardware observations and uncertainties are recorded in [deployment notes](deployment_notes.md).
