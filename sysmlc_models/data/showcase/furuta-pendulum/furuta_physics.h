/* External functions backing the Furuta pendulum's calc defs in C. */
#ifndef FURUTA_PHYSICS_H
#define FURUTA_PHYSICS_H

#include "furutaSystem_types.h"

double restrict_angle(double theta);
furuta_pendulum_pendulum_state_t step(
    furuta_pendulum_pendulum_state_t x, double u, double dt);
double swingup_torque(furuta_pendulum_angle_reading_t r);
double catch_torque(furuta_pendulum_angle_reading_t r);
double stabilize_torque(furuta_pendulum_angle_reading_t r);

#endif /* FURUTA_PHYSICS_H */
