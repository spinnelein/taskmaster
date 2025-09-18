# TaskMaster Enhanced Data Structures

## Overview

This document describes the enhanced data structures implemented in TaskMaster to support sophisticated project management, meal planning, and task scheduling capabilities.

## Core Data Models

### 1. Events (Time Pool Creators)
**Purpose**: Create walls that form pools of time for task scheduling.

**Key Features**:
- **Blocking vs Non-blocking**: Events can prevent tasks from being scheduled (blocking) or be informational only (non-blocking)
- **Multitasking Support**: Some events allow tasks to run concurrently
- **Buffer Times**: Events can have buffer time before/after to prevent scheduling conflicts
- **Flexibility**: Events can be marked as moveable for automatic rescheduling
- **Types**: Meeting, appointment, deadline, personal, work, travel, meal, break, exercise, custom

**Relationships**:
- Can belong to Projects
- 1:1 relationship with Meals (for dinner events)

### 2. Tasks (Time Pool Fillers)
**Purpose**: Main building blocks that fill available time pools created by events.

**Enhanced Features**:
- **Conditions**: Weather requirements, context needs (home/office/phone), equipment dependencies
- **Dependencies**: Tasks can depend on other tasks, creating scheduling chains
- **Divisibility**: Tasks can be marked as divisible into smaller chunks
- **Queue Management**: Tasks maintain queue positions and can be auto-scheduled
- **Status System**: Active, Blocked, Completed (simplified 3-status system)
- **Priority Levels**: Low, Medium, High, Critical
- **Cost Tracking**: Estimated and actual costs

**Relationships**:
- Can belong to Initiatives, Projects, Project Phases, or Meals
- Can have dependencies with other tasks

### 3. Initiatives (Recurring Task Sets)
**Purpose**: Sets of recurring or non-recurring tasks (e.g., weekly meal planning, monthly reviews).

**Features**:
- **Frequency Options**: Daily, weekly, monthly, quarterly, yearly, custom
- **Template System**: Can be marked as templates for creating new initiatives
- **Status Management**: Active, paused, completed, archived
- **Scheduling**: Preferred start times and duration estimates

**Relationships**:
- Contains multiple Tasks
- Can have one associated Project

### 4. Projects & Project Phases
**Purpose**: Series of tasks/events broken into phases with dependencies.

**Project Features**:
- **Multi-phase Organization**: Projects are broken into ordered phases
- **Status Tracking**: Planning, active, on hold, completed, cancelled
- **Timeline Management**: Estimated and actual start/end dates
- **Priority Levels**: Low, medium, high, critical
- **Template Support**: Can be created from Project Templates

**Phase Features**:
- **Ordered Phases**: Each phase has a specific order within the project
- **Phase Dependencies**: Phases can depend on other phases
- **Independent Timeline**: Each phase has its own timeline
- **Task Organization**: Tasks can be assigned to specific phases

**Relationships**:
- Projects contain multiple Phases
- Phases contain multiple Tasks
- Projects can have associated Events
- Projects can belong to Initiatives

### 5. Project Templates (Reusable Blueprints)
**Purpose**: Reusable command scripts that create complete projects with phases, tasks, and events.

**Features**:
- **Template Categories**: Personal, work, home, creative, learning, health, custom
- **Version Control**: Templates have version numbers and can reference parent templates
- **Execution Scripts**: Command scripts that create project structures
- **Usage Tracking**: Track how many times templates have been used
- **Public Sharing**: Templates can be marked as public for sharing

**Components**:
- **Phases Template**: JSON structure for creating phases
- **Tasks Template**: JSON structure for creating tasks
- **Events Template**: JSON structure for creating events
- **Execution Log**: Track template execution success/failure

### 6. Meals (1:1 with Dinner Events)
**Purpose**: Associated 1:1 with dinner events, contain dishes and generate prep tasks.

**Features**:
- **Meal Types**: Breakfast, lunch, dinner, snack, dessert
- **Status Tracking**: Planned, shopping, prepping, cooking, served, cancelled
- **Timeline Management**: Planned date, prep start, cook start, serve time
- **Nutrition Tracking**: Calorie estimates and dietary tags
- **Cost Tracking**: Estimated and actual costs
- **Serving Management**: Number of servings planned

**Relationships**:
- 1:1 relationship with Events (dinner events)
- Contains multiple Dishes (many-to-many)
- Generates prep Tasks automatically

### 7. Dishes & Recipes
**Purpose**: Have recipes, ingredients, and generate prep tasks (e.g., "take rolls out 6 hours before").

**Dish Features**:
- **Classification**: Main, side, appetizer, dessert, beverage, sauce, bread
- **Difficulty Levels**: Very easy, easy, medium, hard, expert
- **Timing**: Prep time, cook time, total time (including wait times)
- **Advance Preparation**: Hours needed in advance (marinating, rising, etc.)
- **Serving Info**: Default servings, calories, cost estimates
- **Dietary Tags**: Vegetarian, dairy-free, gluten-free, etc.

**Recipe Features**:
- **Structured Content**: JSON-based ingredients, instructions, equipment lists
- **Source Tracking**: URL, book, person who provided the recipe
- **Versioning**: Recipe versions and variations (parent-child relationships)
- **Prep Task Generation**: Automatic creation of preparation tasks

**Additional Models**:
- **Ingredients**: Master list with storage info, nutritional data, cost tracking
- **Prep Task Templates**: Templates for generating time-sensitive prep tasks

## Relationships Overview

```
Initiative (1) -> (N) Tasks
Initiative (1) -> (1) Project

Project (1) -> (N) Project Phases
Project (1) -> (N) Tasks  
Project (1) -> (N) Events
Project (1) -> (1) Project Template

Project Phase (1) -> (N) Tasks

Event (1) -> (1) Meal

Meal (N) -> (N) Dishes (via MealDish join table)
Meal (1) -> (N) Tasks (generated prep tasks)

Dish (1) -> (1) Recipe
Recipe (1) -> (N) Prep Task Templates

Task -> Task (Dependencies via TaskDependency table)
```

## Key Design Principles

1. **Time Pool Management**: Events create walls that form time pools, tasks fill those pools
2. **Flexible Dependencies**: Both tasks and project phases support dependency relationships
3. **Auto-generation**: Meals generate prep tasks, templates create project structures
4. **Comprehensive Tracking**: Cost, time, status tracking across all entities
5. **Template System**: Reusable patterns for initiatives, projects, and prep tasks
6. **Context Awareness**: Tasks understand weather, location, and equipment requirements

## Usage Patterns

1. **Project Management**: Create project templates, execute them to generate projects with phases and tasks
2. **Meal Planning**: Plan meals, automatically generate prep tasks based on recipe requirements
3. **Recurring Work**: Use initiatives to manage recurring task sets (weekly planning, monthly reviews)
4. **Time Scheduling**: Events create time boundaries, task scheduler fills gaps with appropriate tasks
5. **Dependency Management**: Complex workflows with task dependencies and phase dependencies

This enhanced data structure provides a comprehensive foundation for sophisticated task and project management while maintaining flexibility for various use cases.