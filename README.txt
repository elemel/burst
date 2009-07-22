Game Design

- The ship can switch between different batteries. Cannon batteries can hold
  one, two, or three cannons. The available batteries are laser, plasma, and
  missile.

- Toggle lock with the enter key. The ship will lock the target that is closest
  to the ray extending forward from the ship. The lock is released when the
  target goes out of range or is destroyed. To switch target explicitly, toggle
  lock twice. Note that this will lock the previous target again if it's still
  the best choice available.

- Lock an enemy missile to jam it.

- The ship will turn to face the locked target. If nothing is locked, the
  ship will face goal. Missiles will seek the locked target.

- The ship has a shield that is on as long as the ship doesn't fire. The shield
  has three power segments. It will only recover power within the same segment.
