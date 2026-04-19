import streamlit as st
from sqlalchemy import text
from datetime import datetime
import time
import plotly.express as px
import pandas as pd

# Initialize connection.
conn = st.connection("postgresql", type="sql")

st.set_page_config(
    page_title="Workout Tracker",
    layout="wide",
)

def main():
    st.title("Workout Tracker")
    st.write("Welcome to the Workout Tracker app! Here you can log your exercises and track your progress over time.")
    # Sidebar navigation
    page = st.sidebar.radio(
        "Go to",
        ["Log Workout", "View Exercise Progress", "New Exercise"],
        index=0,
    )

    if page == "New Exercise":
        new_exercise()
    elif page == "View Exercise Progress":
        view_exercise_progress()
    else:
        log_workout_sets()

def new_exercise():
    st.title("Add New Exercise")
    with st.form("my_form", clear_on_submit=True):
        exercise = st.text_input('What would you like to name the new exercise? ', max_chars=30)
        #desc_toggle = st.checkbox("Would you like to write a description?")
        #desc = ""
        #if desc_toggle:
        desc = st.text_input('Description (Optional)')
        if st.form_submit_button('Submit'):
            if exercise == "":
                st.error("Please enter an exercise name.")
                return
            if desc == "":
                desc = None
            try:
                with conn.session as session:
                    query = text("INSERT INTO exercises (name, description) VALUES (:exercise, :desc)")
                    session.execute(query, {"exercise": exercise.title(), "desc": desc})
                    session.commit()
                st.success(f'Exercise "{exercise.title()}" added to database!')
            except Exception as e:
                st.error(f'Error adding exercise: {e}')

def view_exercise_progress():
    st.title("Exercise Progress")
    st.markdown("Select an exercise to view your progress over time.")
    exercise_options = []
    try:
        df = conn.query("SELECT name, id FROM exercises")
        exercise_options_w_id = [(row[1], row[2]) for row in df.itertuples()]
        exercise_options = [row[1] for row in df.itertuples()]
    except Exception as e:
        st.error(f'Error fetching exercises: {e}')
        return

    if not exercise_options:
        st.warning("No exercises found. Please add an exercise first.")
        return
    exercise = st.selectbox("Exercise", options=exercise_options)

    exercise_id = None
    for ex_option in exercise_options_w_id:
        if ex_option[0] == exercise:
            exercise_id = ex_option[1]
            break

    metric = st.radio("Metric to Plot", options=["Max Weight", "Total Volume"], index=0)
    units = st.radio("Units", options=["Pounds", "Kilograms"], index=0)
    try:
        with conn.session as session:
            query = text("""
                SELECT w.date, w.id AS workout_id, ei.weight_lbs, ei.weight_kg, ei.reps
                FROM exercise_instances ei
                JOIN workouts w ON ei.workout_id = w.id
                WHERE ei.exercise_id = :exercise_id
                ORDER BY w.date
            """)
            result = session.execute(query, {"exercise_id": exercise_id}).fetchall()
    except Exception as e:
        st.error(f'Error fetching exercise data: {e}')
        return

    # Convert result to a DataFrame for easier manipulation
    df = pd.DataFrame(result, columns=["date", "workout_id", "weight_lbs", "weight_kg", "reps"])

    # Plot the data
    if metric == "Max Weight" and units == "Pounds":
        df_plot = df.groupby("date")["weight_lbs"].max().reset_index()
        fig = px.line(df_plot, x="date", y="weight_lbs", title="Max Weight Over Time", labels={"weight_lbs": "Weight (lbs)", "date": "Date"})
    elif metric == "Max Weight" and units == "Kilograms":
        df_plot = df.groupby("date")["weight_kg"].max().reset_index()
        fig = px.line(df_plot, x="date", y="weight_kg", title="Max Weight Over Time", labels={"weight_kg": "Weight (kg)", "date": "Date"})
    elif metric == "Total Volume" and units == "Pounds":
        df["volume_lbs"] = df["weight_lbs"] * df["reps"]
        df_plot = df.groupby("date")["volume_lbs"].sum().reset_index()
        fig = px.line(df_plot, x="date", y="volume_lbs", title="Total Volume Over Time", labels={"volume_lbs": "Volume (lbs)", "date": "Date"})
    elif metric == "Total Volume" and units == "Kilograms":
        df["volume_kg"] = df["weight_kg"] * df["reps"]
        df_plot = df.groupby("date")["volume_kg"].sum().reset_index()
        fig = px.line(df_plot, x="date", y="volume_kg", title="Total Volume Over Time", labels={"volume_kg": "Volume (kg)", "date": "Date"})

    st.plotly_chart(fig)


def _init_state():
    if "current_exercise_sets" not in st.session_state:
    #     # list of dicts, each dict holds values for one set
        st.session_state.current_exercise_sets = []
    # if "logged_exercises" not in st.session_state:
    #     st.session_state.logged_exercises = []
    if "current_exercises" not in st.session_state:
        st.session_state.current_exercises = []  # list of dicts, each dict represents an exercise with its sets

def add_empty_exercise():
    st.session_state.current_exercises.append({"exercise_name": None, "sets": []}) 
    st.session_state.current_exercises[-1]["id"] = len(st.session_state.current_exercises)-1  # unique id for keys

def add_empty_set(idx):
    # Append a new empty set entry; inputs will be rendered with unique keys
    st.session_state.current_exercise_sets.append({
        "weight": None,
        "reps": None,
        "rpe": None,
        "id": datetime.now().timestamp(),  # unique id for keys,
        "ex_id": idx
    })
    for ex in st.session_state.current_exercises:
        if ex["id"] == idx:
            ex["sets"].append(st.session_state.current_exercise_sets[-1])  # link set to exercise
            break

def remove_exercise(idx):
    st.session_state.current_exercises.pop(idx)
    st.session_state.current_exercise_sets = [
        s for s in st.session_state.current_exercise_sets if s["ex_id"] != idx
        ]

def remove_set(set_id, ex_id):
    st.session_state["current_exercise_sets"] = [
        s for s in st.session_state["current_exercise_sets"] if s["id"] != set_id
    ]
    # Also remove from the exercise's sets
    st.session_state["current_exercises"][ex_id]["sets"] = [
        s for s in st.session_state["current_exercises"][ex_id]["sets"] if s["id"] != set_id
    ]

def save_exercise(workout_date):
    if not st.session_state.current_exercises:
        st.error("Please add at least one exercise.")
        return
    if not st.session_state.current_exercise_sets:
        st.error("Add at least one set before saving.")
        return

    try:
        with conn.session as session:
            query = text("INSERT INTO workouts(date) VALUES (:date) RETURNING id")
            workout_id = session.execute(query, {"date": workout_date}).scalar_one()  # get the id of the newly created workout
            session.commit()
    except Exception as e:
        st.error(f'Error uploading workout: {e}')
        return
    
    for exercise in st.session_state.current_exercises:
        exercise_id_postgres = exercise["exercise_id_postgres"]
        for i, set in enumerate(exercise["sets"]):
            weight_lbs = set["weight"]
            weight_kg = round(weight_lbs/2.21, 2)
            set_num = i+1
            reps = set["reps"]
            rpe = set["rpe"]
            try:
                with conn.session as session:
                    query = text("INSERT INTO exercise_instances(workout_id, exercise_id, set_num, reps, " \
                    "weight_lbs, weight_kg, rpe) VALUES (:workout_id, :exercise_id, :set_num, :reps, " \
                    ":weight_lbs, :weight_kg, :rpe)")
                    param_dict = {
                        "workout_id": workout_id,
                        "exercise_id": exercise_id_postgres,
                        "set_num": set_num,
                        "reps": reps,
                        "weight_lbs": weight_lbs,
                        "weight_kg": weight_kg,
                        "rpe": rpe
                    }
                    session.execute(query, param_dict)
                    session.commit()
            except Exception as e:
                st.error(f'Error uploading exercise "{exercise["exercise_name"]}" set {set_num}: {e}')
                return

    # clear current sets and input name
    st.session_state.current_exercise_sets = []
    st.session_state.current_exercises = []
    st.success(f"Saved workout for {workout_date}!")
    time.sleep(2)
    st.rerun()

def log_workout_sets():
    _init_state()
    st.title("Log Workout")

    # st.subheader("Add an Exercise")
    
    exercise_options = []
    try:
        df = conn.query("SELECT name, id FROM exercises")
        exercise_options_w_id = [(row[1], row[2]) for row in df.itertuples()]
        exercise_options = [row[1] for row in df.itertuples()]
    except Exception as e:
        st.error(f'Error fetching exercises: {e}')
        return

    if not exercise_options:
        st.warning("No exercises found. Please add an exercise first.")
        return
    
    workout_date = st.date_input("Date of Workout", value=datetime.today())
    st.subheader("Add an Exercise")

    # Add and Clear Exercise buttons
    add_exercise, clear_exercise = st.columns([1, 1])
    with add_exercise:
        if st.button("Add Exercise"):
            add_empty_exercise()
    with clear_exercise:
        if st.button("Clear Exercises"):
            st.session_state.current_exercises = []

    # Exercise selection for the most recently added exercise
    st.markdown("**Select Exercise**")
    if not st.session_state.current_exercises:
        st.info("No exercise added yet. Click Add Exercise to create one.")
        return
    else:
        # Render exercise selection for the most recently added exercise
        for idx, ex in enumerate(st.session_state.current_exercises):
            ex_key_prefix = f"exercise_{ex['id']}"
            ex_col1, ex_col2 = st.columns([3, 1])
            with ex_col1:
                exercise_name = st.selectbox(f"Exercise {idx+1}", options=exercise_options, 
                                             key=f"{ex_key_prefix}_select")
            with ex_col2:                
                if st.button(f"Remove Exercise", key=f"{ex_key_prefix}_remove"):
                    remove_exercise(idx)
                    st.rerun()
            st.session_state.current_exercises[idx]["exercise_name"] = exercise_name
            for ex_option in exercise_options_w_id:
                if ex_option[0] == exercise_name:
                    st.session_state.current_exercises[idx]["exercise_id_postgres"] = ex_option[1]
                    break

            # Buttons to add a set or clear all sets
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Add set", key=f"{ex_key_prefix}_add_set"):
                    add_empty_set(ex['id'])
            with col2:
                if st.button("Clear sets", key=f"{ex_key_prefix}_clear_sets"):
                    #st.write(st.session_state.current_exercises[idx])
                    st.session_state.current_exercises[idx]["sets"] = []

            st.markdown("**Sets**")
            if not st.session_state.current_exercise_sets:
                st.info("No sets yet. Click Add set to create one.")
            else:
                # Render each set as a row of inputs
                for idx_set, s in enumerate(st.session_state.current_exercises[idx]["sets"]):
                    key_prefix = f"{ex_key_prefix}_set_{s['id']}"
                    cols = st.columns([1, 1, 1, 0.4])
                    with cols[0]:
                        # weight as number input (allow float)
                        s["weight"] = st.number_input("Weight", min_value=0.0, step=0.5, format="%.1f",
                                        key=f"{key_prefix}_weight", value=s.get("weight") or 0.0)
                    with cols[1]:
                        s["reps"] = st.number_input("Reps", min_value=0, step=1, key=f"{key_prefix}_reps",
                                                    value=s.get("reps") or 0)
                    with cols[2]:
                        s["rpe"] = st.number_input("RPE", min_value=0.0, max_value=10.0, step=0.5, format="%.1f",
                                        key=f"{key_prefix}_rpe", value=s.get("rpe") or 0.0)
                    with cols[3]:
                        # Remove button for this set
                        remove_label = f"Remove" #{idx_set+1}"
                        if st.button(remove_label, key=f"{key_prefix}_remove"):
                            remove_set(s["id"], s["ex_id"])
                            st.rerun()

    # Save workout
    if st.button("Save Workout"):
        save_exercise(workout_date)


if __name__ == "__main__":
    main()