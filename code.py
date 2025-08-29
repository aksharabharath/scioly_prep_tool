import streamlit as st
import pandas as pd
import random
import io # Import the io module
import os
import time

# --- Custom CSS for Red Exit Button ---
st.markdown("""
<style>
/* This targets the specific "Exit Drill" button using its data-testid */
[data-testid="stButton-exit_drill_button"] > button {
    background-color: #ff4b4b;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_questions():
    """Loads the question data from st.secrets."""
    try:
        csv_content = st.secrets.get("questions_full.csv")
        if csv_content is None:
            st.error("Error: The file 'questions_full.csv' was not found in st.secrets. Please ensure you have added it as a secret in your app's settings.")
            return []
            
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Combine individual option columns into a single 'options' list
        option_cols = [col for col in df.columns if col.startswith('options__')]
        if not option_cols:
            st.error("Error: 'options__' columns not found in the CSV data.")
            return []
            
        df['options'] = df[option_cols].apply(
            lambda row: [str(item).strip() for item in row if pd.notna(item)], 
            axis=1
        )
        df = df.drop(columns=option_cols)
        
        # Infer question type based on options
        df['type'] = df['options'].apply(lambda x: 
            'true/false' if set(x) == {'True', 'False'} else
            'multiple-choice' if len(x) > 1 else
            'short-answer'
        )
        
        # Clean up the dataframe and return as a list of dictionaries
        questions_list = df.to_dict('records')
        
        # Filter out any rows that are missing 'event' or 'topic' keys
        questions_list = [q for q in questions_list if 'event' in q and 'topic' in q and pd.notna(q['event']) and pd.notna(q['topic'])]
        
        return questions_list
    
    except (pd.errors.EmptyDataError, KeyError) as e:
        st.error(f"Error reading CSV: {e}. Please ensure the secret has the correct columns and data format.")
        return []        
        # Combine individual option columns into a single 'options' list
        option_cols = [col for col in df.columns if col.startswith('options__')]
        if not option_cols:
            st.error("Error: 'options__' columns not found in the CSV data.")
            return []
            
        df['options'] = df[option_cols].apply(
            lambda row: [str(item).strip() for item in row if pd.notna(item)], 
            axis=1
        )
        df = df.drop(columns=option_cols)
        
        # Infer question type based on options
        df['type'] = df['options'].apply(lambda x: 
            'true/false' if set(x) == {'True', 'False'} else
            'multiple-choice' if len(x) > 1 else
            'short-answer'
        )
        
        # Clean up the dataframe and return as a list of dictionaries
        questions_list = df.to_dict('records')
        
        # Filter out any rows that are missing 'event' or 'topic' keys
        questions_list = [q for q in questions_list if 'event' in q and 'topic' in q and pd.notna(q['event']) and pd.notna(q['topic'])]
        
        return questions_list
    
    except (pd.errors.EmptyDataError, KeyError) as e:
        st.error(f"Error reading CSV: {e}. Please ensure the secret has the correct columns and data format.")
        return []

# --- Initialize Session State ---
def initialize_session_state():
    """Initializes all necessary session state variables."""
    if 'questions_data' not in st.session_state:
        st.session_state.questions_data = load_questions()
    if 'event' not in st.session_state:
        st.session_state.event = None
    if 'selected_topics' not in st.session_state:
        st.session_state.selected_topics = []
    if 'questions_list' not in st.session_state:
        st.session_state.questions_list = []
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'attempted_questions' not in st.session_state:
        st.session_state.attempted_questions = 0
    if 'incorrect_questions' not in st.session_state:
        st.session_state.incorrect_questions = []
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'last_answer_state' not in st.session_state:
        st.session_state.last_answer_state = None
    if 'show_cheat_sheet' not in st.session_state:
        st.session_state.show_cheat_sheet = False
    if 'hint_revealed' not in st.session_state:
        st.session_state.hint_revealed = False
    if 'awaiting_action_after_incorrect' not in st.session_state:
        st.session_state.awaiting_action_after_incorrect = False
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = ""
    if 'topic_stats' not in st.session_state:
        st.session_state.topic_stats = {}
    if 'hints_used' not in st.session_state:
        st.session_state.hints_used = 0
    if 'show_exit_confirmation' not in st.session_state:
        st.session_state.show_exit_confirmation = False
    if 'mode' not in st.session_state:
        st.session_state.mode = None
    if 'timer_end_time' not in st.session_state:
        st.session_state.timer_end_time = None
    if 'extra_minute_used' not in st.session_state:
        st.session_state.extra_minute_used = False

# --- Callback Functions ---
def set_event(event_name):
    """Callback to set the event and move to the next screen."""
    st.session_state.event = event_name

def start_drill():
    """Callback to get questions and start the drill."""
    st.session_state.questions_list = get_questions_for_event(st.session_state.event, st.session_state.selected_topics)
    st.session_state.current_question_index = 0
    st.session_state.show_cheat_sheet = False
    st.session_state.hint_revealed = False
    st.session_state.show_answer = False
    st.session_state.last_answer_state = None
    st.session_state.awaiting_action_after_incorrect = False
    st.session_state.user_answer = ""
    st.session_state.topic_stats = {}
    st.session_state.hints_used = 0
    st.session_state.show_exit_confirmation = False
    
    # Reset timer for Timed Drill
    if st.session_state.mode == "Timed Drill":
        st.session_state.timer_end_time = time.time() + 60
        st.session_state.extra_minute_used = False

def check_answer_callback():
    """Checks the user's answer and updates the score."""
    current_question = st.session_state.questions_list[st.session_state.current_question_index]
    correct_answer = current_question['answer']
    
    # Update topic stats
    topic = current_question['topic']
    if topic not in st.session_state.topic_stats:
        st.session_state.topic_stats[topic] = {'attempted': 0, 'correct': 0}
        
    st.session_state.topic_stats[topic]['attempted'] += 1
    st.session_state.attempted_questions += 1
    
    if str(st.session_state.user_answer).strip().lower() == str(correct_answer).strip().lower():
        st.session_state.score += 1
        st.session_state.topic_stats[topic]['correct'] += 1
        st.session_state.last_answer_state = 'correct'
        st.session_state.show_answer = True
    else:
        st.session_state.last_answer_state = 'incorrect'
        st.session_state.awaiting_action_after_incorrect = True

def next_question():
    """Moves to the next question in the list."""
    st.session_state.current_question_index += 1
    st.session_state.show_answer = False
    st.session_state.last_answer_state = None
    st.session_state.hint_revealed = False
    st.session_state.awaiting_action_after_incorrect = False
    st.session_state.user_answer = ""
    st.session_state.show_exit_confirmation = False
    st.session_state.extra_minute_used = False # Reset extra minute for new question
    
    # Reset timer for Timed Drill
    if st.session_state.mode == "Timed Drill":
        st.session_state.timer_end_time = time.time() + 60

def return_to_event_selection():
    """Resets all state and returns to the event selection screen."""
    st.session_state.event = None
    st.session_state.questions_list = []
    st.session_state.current_question_index = 0
    st.session_state.score = 0
    st.session_state.attempted_questions = 0
    st.session_state.incorrect_questions = []
    st.session_state.show_answer = False
    st.session_state.selected_topics = []
    st.session_state.last_answer_state = None
    st.session_state.show_cheat_sheet = False
    st.session_state.hint_revealed = False
    st.session_state.awaiting_action_after_incorrect = False
    st.session_state.user_answer = ""
    st.session_state.topic_stats = {}
    st.session_state.hints_used = 0
    st.session_state.show_exit_confirmation = False
    st.session_state.mode = None # Reset mode
    st.session_state.timer_end_time = None
    st.session_state.extra_minute_used = False

def reset_practice_session():
    """Resets the state for a new practice session."""
    st.session_state.questions_list = []
    st.session_state.current_question_index = 0
    st.session_state.score = 0
    st.session_state.attempted_questions = 0
    st.session_state.incorrect_questions = []
    st.session_state.show_answer = False
    st.session_state.selected_topics = []
    st.session_state.last_answer_state = None
    st.session_state.show_cheat_sheet = False
    st.session_state.hint_revealed = False
    st.session_state.awaiting_action_after_incorrect = False
    st.session_state.user_answer = ""
    st.session_state.topic_stats = {}
    st.session_state.hints_used = 0
    st.session_state.show_exit_confirmation = False
    st.session_state.timer_end_time = None
    st.session_state.extra_minute_used = False

def toggle_cheat_sheet(state):
    """Callback to show/hide the cheat sheet."""
    st.session_state.show_cheat_sheet = state

def show_hint():
    """Callback to show the hint and allow re-answering."""
    st.session_state.hint_revealed = True
    st.session_state.awaiting_action_after_incorrect = False
    st.session_state.user_answer = ""
    st.session_state.show_answer = False
    st.session_state.hints_used += 1

def reveal_answer():
    """Callback to reveal the answer and move to the next question."""
    st.session_state.show_answer = True
    st.session_state.awaiting_action_after_incorrect = False
    current_question = st.session_state.questions_list[st.session_state.current_question_index]
    st.session_state.incorrect_questions.append(current_question)
    if st.session_state.mode == "Timed Drill":
        st.session_state.timer_end_time = None

def add_extra_minute():
    """Callback to give the user one more minute."""
    st.session_state.timer_end_time = time.time() + 60
    st.session_state.extra_minute_used = True
    st.session_state.awaiting_action_after_incorrect = False
    st.session_state.user_answer = ""

def show_exit_confirmation():
    """Callback to trigger the exit confirmation popup."""
    st.session_state.show_exit_confirmation = True

# --- Helper Functions ---
def get_questions_for_event(event_name, topics):
    """
    Gathers questions for a selected event and topics, then shuffles them.
    Includes logic to select a quota of questions per topic.
    """
    if not st.session_state.questions_data:
        return []
    
    event_questions = [q for q in st.session_state.questions_data if q['event'] == event_name]
    
    final_questions = []
    
    # If all topics are selected, or no topics are selected, use all questions
    if 'All of the Above' in topics or not topics:
        final_questions = event_questions
    else:
        # Loop through each selected topic and grab a maximum of 5 questions
        for topic in topics:
            topic_questions = [q for q in event_questions if q['topic'] == topic]
            random.shuffle(topic_questions)
            final_questions.extend(topic_questions[:5])
    
    random.shuffle(final_questions)
    
    # Final check for total question count
    if len(final_questions) >= 10:
        return final_questions[:10]  # Return the first 10 questions
    else:
        return final_questions      # Return all available questions if less than 10

def generate_cheat_sheet_phrase(question_data):
    """Generates a concise phrase for the cheat sheet."""
    # Prioritize explanation if it exists, otherwise fall back to Q&A
    if 'explanation' in question_data and pd.notna(question_data['explanation']):
        return question_data['explanation']
    else:
        return f"Q: {question_data['question']}\nA: {question_data['answer']}"

# --- UI Layout and Logic ---
st.set_page_config(page_title="SciOly Prep Tool", layout="centered", page_icon="✨")

st.title("SciOly Prep Tool")
st.markdown("---")

initialize_session_state()

# Main conditional block to control page flow
# The logic here has been simplified to prevent the premature jump.
if st.session_state.event is None:
    # Home Page: Event Selection
    st.header("Select an Event to Begin")
    st.markdown("### Welcome to the Science Olympiad Preparation Tool!")
    st.markdown("Use this app to study for your events by taking practice drills.")
    
    if st.session_state.questions_data:
        event_name = "Astronomy"
        if st.button("Astronomy", use_container_width=True, on_click=set_event, args=(event_name,)):
            pass
    else:
        st.warning("No question data found.")

elif not st.session_state.questions_list:
    # Mode and Topic Selection
    st.header(f"Select Mode and Topics for {st.session_state.event} 📚")
    
    st.session_state.mode = st.radio(
        "Choose your drill mode:",
        options=["Study Mode", "Timed Drill"],
        index=0,
    )

    if st.session_state.questions_data:
        topics = sorted(list(set(q['topic'] for q in st.session_state.questions_data if q['event'] == st.session_state.event)))
        
        st.session_state.selected_topics = st.multiselect(
            "Choose one or more topics:",
            options=["All of the Above"] + topics,
            default=["All of the Above"]
        )

        if st.button("Start Drill", use_container_width=True, on_click=start_drill):
            pass
        
        st.button("Back to Events", on_click=return_to_event_selection)
    else:
        st.warning("No questions loaded for this event.")
        st.button("Back to Events", on_click=return_to_event_selection)

else:
    # Practice Mode (Study Mode or Timed Drill)
    st.header(f"Practice Mode: {st.session_state.event} ({st.session_state.mode}) ✨")
    
    # Conditional logic for Exit Confirmation
    if st.session_state.show_exit_confirmation:
        with st.container(border=True):
            st.warning("Are you sure you want to exit? Your current progress will be lost.")
            col1, col2 = st.columns(2)
            with col1:
                st.button("❌ Exit", on_click=return_to_event_selection, use_container_width=True)
            with col2:
                st.button("✅ Stay", on_click=lambda: st.session_state.update(show_exit_confirmation=False), use_container_width=True)
    else:
        # Display cheat sheet if the user has opted to view it
        if st.session_state.show_cheat_sheet:
            st.subheader("Current Cheat Sheet")
            if st.session_state.incorrect_questions:
                # Generate the cheat sheet text for display
                cheat_sheet_text = ""
                for q_data in st.session_state.incorrect_questions:
                    phrase = generate_cheat_sheet_phrase(q_data)
                    cheat_sheet_text += f"- {phrase}\n\n"
                
                # Display the text in the app
                st.text_area("Cheat Sheet Content", value=cheat_sheet_text, height=400, disabled=True)
                
                # Provide download buttons
                st.download_button(
                    label="Download as Plain Text (.txt)",
                    data=cheat_sheet_text,
                    file_name=f"SciOly_{st.session_state.event}_CheatSheet.txt",
                    mime="text/plain"
                )

                # Generate markdown content for download
                markdown_content = ""
                for q_data in st.session_state.incorrect_questions:
                    markdown_content += f"- {generate_cheat_sheet_phrase(q_data)}\n\n"
                
                st.download_button(
                    label="Download as Markdown (.md)",
                    data=markdown_content,
                    file_name=f"SciOly_{st.session_state.event}_CheatSheet.md",
                    mime="text/markdown"
                )

            else:
                st.info("Your cheat sheet is empty. Keep going!")
            
            if st.button("Return to Drill", on_click=toggle_cheat_sheet, args=(False,)):
                pass
                
        # Display current question if not showing cheat sheet
        elif st.session_state.questions_list and st.session_state.current_question_index < len(st.session_state.questions_list):
            question_data = st.session_state.questions_list[st.session_state.current_question_index]
            
            progress_percentage = (st.session_state.current_question_index / len(st.session_state.questions_list))
            st.progress(progress_percentage, text=f"Question {st.session_state.current_question_index + 1} of {len(st.session_state.questions_list)}")
            
            st.subheader(f"Topic: {question_data['topic']}")
            
            # Timed Drill Timer
            if st.session_state.mode == "Timed Drill" and not st.session_state.awaiting_action_after_incorrect:
                timer_placeholder = st.empty()
                
                time_left = st.session_state.timer_end_time - time.time()
                
                if time_left <= 0:
                    st.session_state.last_answer_state = 'incorrect'
                    st.session_state.awaiting_action_after_incorrect = True
                    timer_placeholder.error("Time's up!")
                else:
                    minutes, seconds = divmod(int(time_left), 60)
                    timer_placeholder.info(f"Time remaining: {minutes:02d}:{seconds:02d}")
                    time.sleep(1)
                    st.rerun()

            st.write(f"**Question:** {question_data['question']}")
            
            # Display hint if it has been revealed (and only if it's not a correct answer)
            if st.session_state.hint_revealed and st.session_state.last_answer_state != 'correct' and 'hint' in question_data and pd.notna(question_data['hint']):
                st.info(f"Hint: {question_data['hint']}")

            # Determine widget based on question type
            if question_data['type'] == 'multiple-choice':
                st.session_state.user_answer = st.radio("Your answer:", question_data['options'], index=None)
            elif question_data['type'] == 'true/false':
                st.session_state.user_answer = st.radio("Your answer:", ['True', 'False'], index=None)
            elif question_data['type'] == 'short-answer':
                st.session_state.user_answer = st.text_input("Your answer:")
                
            # UI for answering the question
            if not st.session_state.show_answer and not st.session_state.awaiting_action_after_incorrect:
                if st.button("Check Answer", use_container_width=True, disabled=st.session_state.user_answer is None, on_click=check_answer_callback):
                    pass
            
            # UI for correct answer
            if st.session_state.last_answer_state == 'correct':
                st.success("✅ Correct!")
                if 'explanation' in question_data and pd.notna(question_data['explanation']):
                    st.info(f"Explanation: {question_data['explanation']}")
                st.button("Next Question", use_container_width=True, on_click=next_question)
                
            # UI for incorrect answer, awaiting user action
            elif st.session_state.awaiting_action_after_incorrect:
                # Timed Drill logic for incorrect/timeout
                if st.session_state.mode == "Timed Drill":
                    st.error("❌ Incorrect or Time's up. Would you like to try again or reveal the answer?")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.button("1 More Minute", use_container_width=True, disabled=st.session_state.extra_minute_used, on_click=add_extra_minute)
                    with col2:
                        st.button("Reveal Answer", use_container_width=True, on_click=reveal_answer)
                # Study Mode logic for incorrect
                else:
                    st.error("❌ Incorrect. Would you like to try again with a hint or reveal the answer?")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.button("Show Hint", use_container_width=True, on_click=show_hint)
                    with col2:
                        st.button("Reveal Answer", use_container_width=True, on_click=reveal_answer)
                    with col3:
                        st.button("Add to Cheat Sheet", use_container_width=True, on_click=lambda: st.session_state.incorrect_questions.append(question_data))
            
            # UI for revealed answer after incorrect action
            elif st.session_state.show_answer and st.session_state.last_answer_state == 'incorrect':
                # Display hint only if the user revealed it
                if st.session_state.hint_revealed and 'hint' in question_data and pd.notna(question_data['hint']):
                    st.info(f"Hint: {question_data['hint']}")
                
                st.error(f"❌ Incorrect. The correct answer is: **{question_data['answer']}**")
                
                if st.session_state.mode == "Timed Drill":
                    st.info("Question has been added to cheat sheet for review.")
                
                if 'explanation' in question_data and pd.notna(question_data['explanation']):
                    st.info(f"Explanation: {question_data['explanation']}")
                st.button("Next Question", use_container_width=True, on_click=next_question)
            
            st.markdown("---")

        else:
            # End of Drill screen
            st.header("Drill Complete! 🎉")
            st.write(f"Fantastic job! You've successfully completed the practice drill for **{st.session_state.event}**.")

            # Overall Summary
            st.subheader("Drill Summary")
            if st.session_state.attempted_questions > 0:
                accuracy = (st.session_state.score / st.session_state.attempted_questions) * 100
                st.write(f"You answered **{st.session_state.score}** out of **{st.session_state.attempted_questions}** questions correctly, for an overall accuracy of **{accuracy:.2f}%**.")
                st.write(f"You used hints **{st.session_state.hints_used}** time(s).")
            else:
                accuracy = 0
                st.write("You didn't answer any questions during this session.")
            
            # Topic-by-topic summary
            if st.session_state.topic_stats:
                st.subheader("Performance by Topic")
                for topic, stats in st.session_state.topic_stats.items():
                    if stats['attempted'] > 0:
                        topic_accuracy = (stats['correct'] / stats['attempted']) * 100
                        st.markdown(f"- **{topic}**: {stats['correct']} of {stats['attempted']} correct ({topic_accuracy:.2f}%)")
                    else:
                        st.markdown(f"- **{topic}**: No questions attempted.")
            
            # Personalized Advice
            st.subheader("Personalized Advice")
            if accuracy >= 80:
                st.success("Your performance is excellent! You have a strong grasp of the material. Keep up the great work and consider exploring new topics or events to broaden your knowledge.")
            elif accuracy >= 50:
                st.info("Great effort! You're on the right track. Focus on reviewing the topics where you had difficulty. Your cheat sheet is a great resource for this. Don't be afraid to try another drill on the same topics to solidify your understanding.")
            else:
                st.warning("You've completed the drill and now have a good starting point. The best next step is to carefully review your personalized cheat sheet and study the explanations for the questions you missed. Remember, every wrong answer is a chance to learn something new!")
            
            # Action Buttons
            st.markdown("---")
            if st.button("Start a New Drill", on_click=return_to_event_selection, use_container_width=True):
                pass

    # Sidebar UI elements
    with st.sidebar:
        st.header("Progress")
        st.write(f"**Score:** {st.session_state.score}")
        st.write(f"**Attempted:** {st.session_state.attempted_questions}")
        if st.session_state.attempted_questions > 0:
            accuracy = (st.session_state.score / st.session_state.attempted_questions) * 100
            st.write(f"**Accuracy:** {accuracy:.2f}%")
        
        # "View Cheat Sheet" button
        if st.button("View Cheat Sheet", use_container_width=True, help="View all incorrect questions so far", on_click=toggle_cheat_sheet, args=(True,)):
            pass

        st.markdown("---")
        
        if st.button("Reset Current Drill", use_container_width=True, help="Clear all progress for this event", on_click=reset_practice_session):
            pass

        # Conditional logic for Exit button with a key for specific styling
        if st.session_state.questions_list and st.session_state.current_question_index / len(st.session_state.questions_list) > 0.5:
            st.button("Exit Drill", key="exit_drill_button", on_click=show_exit_confirmation, use_container_width=True, help="End the current drill and return to event selection")
        else:
            st.button("Exit Drill", key="exit_drill_button", on_click=return_to_event_selection, use_container_width=True, help="End the current drill and return to event selection")
