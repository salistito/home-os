-- Users
CREATE TABLE IF NOT EXISTS users (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  name             TEXT NOT NULL UNIQUE,
  role             TEXT NOT NULL DEFAULT 'member',
  password_hash    TEXT,
  telegram_chat_id TEXT,
  deleted_at       TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_unique_name
ON users(name);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  name           TEXT NOT NULL,
  points         INTEGER NOT NULL,
  frequency_days INTEGER,
  next_due_date  TEXT,
  deleted_at     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_tasks_unique_name
ON tasks(name)
WHERE deleted_at IS NULL;

-- Assignments
CREATE TABLE IF NOT EXISTS assignments (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id               INTEGER NOT NULL,
  user_id               INTEGER NOT NULL,
  assigned_at           TEXT NOT NULL,
  status                TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
  completed_at          TEXT,
  points_awarded        INTEGER,
  source                TEXT NOT NULL DEFAULT 'task' CHECK (source IN ('task', 'cooking')),
  source_entity_id      INTEGER,
  source_entity_details TEXT,

  FOREIGN KEY (task_id) REFERENCES tasks(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_pending_assignment_per_task
ON assignments(task_id)
WHERE status = 'pending';

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_completed_task_assignment_per_day
ON assignments(task_id, assigned_at)
WHERE status = 'completed' AND source = 'task';

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_completed_cooking_assignment_per_event
ON assignments(source_entity_id)
WHERE status = 'completed' AND source = 'cooking';

-- Reminders
CREATE TABLE IF NOT EXISTS reminders (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id               INTEGER NOT NULL,
  message               TEXT NOT NULL,
  trigger_at            TEXT NOT NULL,
  trigger_time          TEXT,
  recurrence            TEXT NOT NULL DEFAULT 'none',
  cron_job_id           TEXT,
  created_at            TEXT NOT NULL,
  owner                 TEXT NOT NULL DEFAULT 'user' CHECK (owner IN ('user', 'system')),
  system_ref_entity     TEXT,
  system_ref_entity_id  TEXT,

  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_reminders_unique_message
ON reminders(user_id, message)
WHERE owner = 'user';

CREATE INDEX IF NOT EXISTS idx_reminders_pending_due
ON reminders(trigger_at);

CREATE INDEX IF NOT EXISTS idx_reminders_system_ref
ON reminders(owner, system_ref_entity, system_ref_entity_id);

-- Finances
CREATE TABLE IF NOT EXISTS finances_periods (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  label     TEXT NOT NULL,
  status    TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
  opened_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_open_period
ON finances_periods(status)
WHERE status = 'open';

CREATE TABLE IF NOT EXISTS finances_entries (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  period_id   INTEGER NOT NULL,
  kind        TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
  scope       TEXT NOT NULL CHECK (scope IN ('shared', 'personal', 'mixed')),
  owner_id    INTEGER NOT NULL,
  label       TEXT NOT NULL,
  amount      INTEGER,
  status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed')),
  paid_at     TEXT,
  detail_mode TEXT NOT NULL DEFAULT 'none' CHECK (detail_mode IN ('none', 'top_down', 'bottom_up')),
  created_at  TEXT NOT NULL,

  FOREIGN KEY (period_id) REFERENCES finances_periods(id),
  FOREIGN KEY (owner_id)  REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_finances_entries_period
ON finances_entries(period_id);

CREATE TABLE IF NOT EXISTS finances_entry_details (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id INTEGER NOT NULL,
  scope    TEXT,
  label    TEXT NOT NULL,
  amount   INTEGER NOT NULL DEFAULT 0,

  FOREIGN KEY (entry_id) REFERENCES finances_entries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_finances_entry_details_entry
ON finances_entry_details(entry_id);

CREATE TABLE IF NOT EXISTS finances_tags (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL UNIQUE COLLATE NOCASE,
  color      TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS finances_entry_tags (
  entry_id INTEGER NOT NULL,
  tag_id   INTEGER NOT NULL,

  PRIMARY KEY (entry_id, tag_id),
  FOREIGN KEY (entry_id) REFERENCES finances_entries(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id)   REFERENCES finances_tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_finances_entry_tags_tag
ON finances_entry_tags(tag_id);

CREATE TABLE IF NOT EXISTS finances_entry_detail_tags (
  detail_id INTEGER NOT NULL,
  tag_id    INTEGER NOT NULL,

  PRIMARY KEY (detail_id, tag_id),
  FOREIGN KEY (detail_id) REFERENCES finances_entry_details(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id)    REFERENCES finances_tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_finances_entry_detail_tags_tag
ON finances_entry_detail_tags(tag_id);

-- Food
CREATE TABLE IF NOT EXISTS food_ingredients (
  id                         INTEGER PRIMARY KEY AUTOINCREMENT,
  name                       TEXT NOT NULL,
  category                   TEXT,
  unit                       TEXT NOT NULL,
  macros                     TEXT NOT NULL DEFAULT '{}',
  purchase_unit              TEXT,
  purchase_conversion_factor REAL,
  external_source            TEXT,
  external_id                TEXT,
  created_at                 TEXT NOT NULL,
  updated_at                 TEXT NOT NULL,
  deleted_at                 TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_food_ingredients_unique_name
ON food_ingredients(name)
WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS food_stock (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  ingredient_id      INTEGER NOT NULL,
  quantity           REAL NOT NULL CHECK(quantity >= 0),
  min_alert_quantity REAL NOT NULL DEFAULT 0,
  expiration_date    TEXT,
  updated_at         TEXT NOT NULL,
  FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_food_stock_ingredient
ON food_stock(ingredient_id);

CREATE TABLE IF NOT EXISTS food_purchases (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ingredient_id INTEGER NOT NULL,
  quantity      REAL NOT NULL CHECK(quantity > 0),
  price         INTEGER NOT NULL CHECK(price >= 0),
  purchased_at  TEXT NOT NULL,
  notes         TEXT,
  created_at    TEXT NOT NULL,
  FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
);

CREATE INDEX IF NOT EXISTS idx_food_purchases_ingredient
ON food_purchases(ingredient_id);

CREATE TABLE IF NOT EXISTS food_recipes (
  id                          INTEGER PRIMARY KEY AUTOINCREMENT,
  name                        TEXT NOT NULL,
  category                    TEXT,
  description                 TEXT,
  portions                    INTEGER NOT NULL CHECK(portions >= 1),
  points_awarded              INTEGER,
  points_min_portions         INTEGER,
  steps                       TEXT,
  created_at                  TEXT NOT NULL,
  updated_at                  TEXT NOT NULL,
  deleted_at                  TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_food_recipes_unique_name
ON food_recipes(name)
WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS food_recipe_ingredients (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id     INTEGER NOT NULL,
  ingredient_id INTEGER NOT NULL,
  quantity      REAL NOT NULL CHECK(quantity > 0),
  unit          TEXT NOT NULL,
  FOREIGN KEY (recipe_id) REFERENCES food_recipes(id) ON DELETE CASCADE,
  FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
);

CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_recipe
ON food_recipe_ingredients(recipe_id);

CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_ingredient
ON food_recipe_ingredients(ingredient_id);

CREATE TABLE IF NOT EXISTS food_cook_events (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id INTEGER NOT NULL,
  user_id   INTEGER NOT NULL,
  portions  INTEGER NOT NULL CHECK(portions >= 1),
  macros    TEXT NOT NULL DEFAULT '{}',
  cooked_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (recipe_id) REFERENCES food_recipes(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_food_cook_events_recipe
ON food_cook_events(recipe_id);

CREATE INDEX IF NOT EXISTS idx_food_cook_events_user
ON food_cook_events(user_id);

CREATE TABLE IF NOT EXISTS food_cook_event_ingredients (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  cook_event_id   INTEGER NOT NULL,
  ingredient_id   INTEGER NOT NULL,
  ingredient_name TEXT NOT NULL,
  quantity        REAL NOT NULL CHECK(quantity > 0),
  unit            TEXT NOT NULL,
  macros          TEXT,
  FOREIGN KEY (cook_event_id) REFERENCES food_cook_events(id) ON DELETE CASCADE,
  FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
);

CREATE INDEX IF NOT EXISTS idx_food_cook_event_ingredients_event
ON food_cook_event_ingredients(cook_event_id);

CREATE INDEX IF NOT EXISTS idx_food_cook_event_ingredients_ingredient
ON food_cook_event_ingredients(ingredient_id);

CREATE TABLE IF NOT EXISTS food_nutrition_goals (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    kcal_target      INTEGER,
    protein_g_target REAL,
    carbs_g_target   REAL,
    fat_g_target     REAL,
    updated_at       TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS food_meal_entries (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL,
  meal_type  TEXT NOT NULL,
  macros     TEXT NOT NULL DEFAULT '{}',
  notes      TEXT,
  eaten_at   TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_food_meal_entries_user
ON food_meal_entries(user_id);

CREATE INDEX IF NOT EXISTS idx_food_meal_entries_eaten_at
ON food_meal_entries(eaten_at);

CREATE TABLE IF NOT EXISTS food_meal_entry_items (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  meal_entry_id INTEGER NOT NULL,
  source        TEXT NOT NULL CHECK (source IN ('cook_event', 'ingredient', 'manual')),
  name          TEXT NOT NULL,
  macros        TEXT NOT NULL DEFAULT '{}',
  cook_event_id INTEGER,
  portions      REAL CHECK(portions > 0),
  ingredient_id INTEGER,
  quantity      REAL CHECK(quantity > 0),
  unit          TEXT,
  FOREIGN KEY (meal_entry_id) REFERENCES food_meal_entries(id) ON DELETE CASCADE,
  FOREIGN KEY (cook_event_id) REFERENCES food_cook_events(id),
  FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
);

CREATE INDEX IF NOT EXISTS idx_food_meal_entry_items_entry
ON food_meal_entry_items(meal_entry_id);

CREATE TABLE IF NOT EXISTS fitness_weight_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    weight_kg   REAL NOT NULL CHECK(weight_kg > 0),
    measured_at TEXT NOT NULL,
    notes       TEXT,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, measured_at)
);

CREATE INDEX IF NOT EXISTS idx_fitness_weight_entries_user
ON fitness_weight_entries(user_id);

CREATE INDEX IF NOT EXISTS idx_fitness_weight_entries_measured_at
ON fitness_weight_entries(measured_at);

CREATE TABLE IF NOT EXISTS fitness_exercise_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    exercise_type   TEXT NOT NULL,
    duration_min    INTEGER CHECK(duration_min > 0),
    intensity       TEXT CHECK(intensity IN ('low', 'medium', 'high')),
    calories_burned REAL,
    performed_at    TEXT NOT NULL,
    notes           TEXT,
    metrics         TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_fitness_exercise_entries_user
ON fitness_exercise_entries(user_id);

CREATE INDEX IF NOT EXISTS idx_fitness_exercise_entries_performed_at
ON fitness_exercise_entries(performed_at);
