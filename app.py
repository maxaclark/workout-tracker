import streamlit as st
from sqlalchemy import text

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
        log_workout()

def new_exercise():
    exercise = st.text_input('What would you like to name the new exercise? ', max_chars=30)
    desc_toggle = st.radio('Would you like to create a description?', ['Yes', 'No'], index=1)
    desc = None
    if desc_toggle == 'Yes':
        desc = st.text_input('Type a short description: ')
    if st.button('Submit'):
        try:
            with conn.session as session:
                query = text("INSERT INTO exercises (name, description) VALUES (:exercise, :desc)")
                session.execute(query, {"exercise": exercise, "desc": desc})
                session.commit()
            st.success(f'Exercise {exercise} added to database!')
            #new_exercise()
        except Exception as e:
            st.error(f'Error adding exercise: {e}')

def view_exercise_progress():
    st.write("This feature is coming soon! Stay tuned for updates.")

def log_workout():
    st.write("This feature is coming soon! Stay tuned for updates.")

if __name__ == "__main__":
    main()