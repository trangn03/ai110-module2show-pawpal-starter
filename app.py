from datetime import time

import streamlit as st
from pawpal_system import Priority, Recurrence, Owner, Task, Pet, Scheduler, format_minutes


def t_end(task: Task) -> str:
    """End time of a task as an HH:MM string."""
    return format_minutes(task.end_minutes)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown("Plan your pets' day by adding tasks, then generate a schedule based on available time.")

# pets is a name -> Pet registry so one owner can manage several pets.
if "pets" not in st.session_state:
    st.session_state.pets = {}

st.divider()

# --- Owner & Pets ---
st.subheader("Owner & Pets")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input("Available time (minutes)", min_value=1, max_value=480, value=60)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    breed = st.text_input("Breed", value="Mixed")

bcol1, bcol2 = st.columns(2)
if bcol1.button("Save owner"):
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))

if bcol2.button("Add / update pet"):
    pets = st.session_state.pets
    # Preserve existing tasks when an already-known pet is re-saved.
    existing_tasks = pets[pet_name].tasks if pet_name in pets else []
    pets[pet_name] = Pet(name=pet_name, breed=breed, tasks=existing_tasks)

if "owner" in st.session_state:
    st.success(f"Owner: {st.session_state.owner.name} ({st.session_state.owner.available_minutes} min available)")
if st.session_state.pets:
    st.caption("Pets: " + ", ".join(st.session_state.pets))

st.divider()

# --- Tasks (stored per pet) ---
st.subheader("Tasks")

if not st.session_state.pets:
    st.info("Add a pet first to start adding tasks.")
else:
    # The pet selector doubles as the "filter by pet name" control.
    selected_name = st.selectbox("Pet", list(st.session_state.pets))
    pet = st.session_state.pets[selected_name]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        start_time = st.time_input("Start time", value=time(8, 0), step=300)
    with col3:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col4:
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    with col5:
        recurrence = st.selectbox("Repeats", ["none", "daily", "weekly"])

    if st.button("Add task"):
        pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=Priority(priority),
                start_time=start_time.strftime("%H:%M"),
                recurrence=Recurrence(recurrence),
            )
        )

    if pet.tasks:
        pet.sort_tasks()

        status = st.radio("Show", ["All", "Pending", "Completed"], horizontal=True)
        if status == "Pending":
            visible = pet.filter_tasks(complete=False)
        elif status == "Completed":
            visible = pet.filter_tasks(complete=True)
        else:
            visible = pet.tasks

        st.write(f"{pet.name}'s tasks (ordered by start time) — showing {len(visible)} of {len(pet.tasks)}:")
        if not visible:
            st.caption("No tasks match this filter.")
        for t in visible:
            c0, c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1, 1])
            c0.write(t.start_time)
            title = t.title
            if t.is_recurring:
                title += f"  🔁 {t.recurrence.value}"
                if t.due_date is not None:
                    title += f" (next: {t.due_date:%b %d})"
            c1.write(title)
            c2.write(f"{t.duration_minutes} min")
            c3.write(t.priority.value)
            c4.write("✅" if t.is_complete else "—")
            if not t.is_complete:
                if c5.button("Done", key=f"done_{id(t)}"):
                    new_task = pet.complete_task(t)
                    if new_task is not None:
                        st.toast(f"Queued next {t.recurrence.value} '{t.title}' for {new_task.due_date:%b %d}")
                    st.rerun()

        # --- Conflict detection for the selected pet ---
        owner = st.session_state.get("owner")
        scheduler = Scheduler(pet=pet, owner=owner) if owner else None
        if scheduler:
            conflicts = scheduler.find_conflicts()
            if conflicts:
                st.warning(f"⚠️ {len(conflicts)} time conflict(s) for {pet.name}:")
                for a, b in conflicts:
                    st.markdown(
                        f"- **{a.title}** ({a.start_time}–{t_end(a)}) overlaps "
                        f"**{b.title}** ({b.start_time}–{t_end(b)})"
                    )

        if st.button("Clear all tasks"):
            for t in list(pet.tasks):
                pet.remove_task(t)
            st.rerun()
    else:
        st.info("No tasks yet. Add one above.")

# --- Owner-wide conflicts across all pets ---
if len(st.session_state.pets) > 1:
    owner_conflicts = Scheduler.find_conflicts_among(list(st.session_state.pets.values()))
    cross = [(pa, ta, pb, tb) for pa, ta, pb, tb in owner_conflicts if pa is not pb]
    if cross:
        st.warning(f"⚠️ {len(cross)} cross-pet conflict(s) — you can't care for two pets at once:")
        for pa, ta, pb, tb in cross:
            st.markdown(
                f"- {pa.name}'s **{ta.title}** ({ta.start_time}–{t_end(ta)}) overlaps "
                f"{pb.name}'s **{tb.title}** ({tb.start_time}–{t_end(tb)})"
            )

st.divider()

# --- Schedule generation ---
st.subheader("Generate Schedule")

if st.button("Generate schedule"):
    if "owner" not in st.session_state:
        st.warning("Save your owner info first.")
    elif not st.session_state.pets:
        st.warning("Add a pet first.")
    else:
        owner = st.session_state.owner
        pet = st.session_state.pets[selected_name]
        if not pet.tasks:
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(pet=pet, owner=owner)
            plan = scheduler.generate_plan()

            if not plan:
                st.warning("No tasks fit within the available time. Try adding shorter tasks or increasing available time.")
            else:
                st.success(f"Schedule for {pet.name} — {owner.name} has {owner.available_minutes} min available.")
                total = 0
                for i, task in enumerate(plan, start=1):
                    total += task.duration_minutes
                    st.markdown(
                        f"**{i}. {task.title}** — {task.duration_minutes} min "
                        f"(priority: {task.priority.value})"
                    )
                st.info(f"Total time scheduled: {total} min out of {owner.available_minutes} min available.")

                skipped = [t for t in pet.tasks if t not in plan and not t.is_complete]
                if skipped:
                    st.markdown("**Skipped (did not fit):**")
                    for t in skipped:
                        st.markdown(f"- {t.title} ({t.duration_minutes} min)")
