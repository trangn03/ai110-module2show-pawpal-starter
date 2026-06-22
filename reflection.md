# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  - Enter owner and pet info which includes pet name, breed, available time per day that the scheduler will be use as constrain
  - Add and manage care tasks which includes create, edit, remove tasks such as feeding, walks, medications, or grooming. Each will have a duration and priority level
  - Generate and view daily plan will use the scheduler to list out the daily schedule for a pet based on entered tasks and constrains.
- What classes did you include, and what responsibilities did you assign to each?
  - There are four classes that I include
    - ```Owner```: pet's owner name, time availability and their request service 
    - ```Pet```: holds pet info, list of task, manages adding, removing, and sorting
    - ```Task```: represents the care activities (name, duration, priority), completion status
    - ```Scheduler```: builds daily schedule based on pet's plan, sort by priority, fit tasks into available time, and delegates task completion

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  - Fill here
- How did you decide which constraints mattered most?
  - Fill here

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
