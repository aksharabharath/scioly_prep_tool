import streamlit as st
import pandas as pd
import random
import os
import time

# --- File Paths ---
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(THIS_FOLDER, "questions_full.csv")

# --- Load Data ---
@st.cache_data
def load_questions(file_path):
    """Loads the question data from a CSV file."""
    if not os.path.exists(file_path):
        st.error(f"Error: The file '{file_path}' was not found. Please ensure the file is in the app's directory and is spelled correctly.")
        return []
    
    try:
        df = pd.read_csv(file_path)
        
        # Combine individual option columns into a single 'options' list
        option_cols = [col for col in df.columns if col.startswith('options__')]
        if not option_cols:
            st.error("Error: 'options__' columns not found in the CSV file.")
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
        st.error(f"Error reading CSV: {e}. Please ensure '{DATA_FILE}' has the correct columns and data format.")
        return []

# --- Initialize Session State ---
def initialize_session_state():
    """Initializes all necessary session state variables."""
    if 'questions_data' not in st.session_state:
        st.session_state.questions_data = load_questions(DATA_FILE)
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

def check_answer_callback():
    """Checks the user's answer and updates the score."""
    current_question = st.session_state.questions_list[st.session_state.current_question_index]
    correct_answer = current_question['answer']
    
    st.session_state.attempted_questions += 1
    
    if str(st.session_state.user_answer).strip().lower() == str(correct_answer).strip().lower():
        st.session_state.score += 1
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

def toggle_cheat_sheet(state):
    """Callback to show/hide the cheat sheet."""
    st.session_state.show_cheat_sheet = state

def show_hint():
    """Callback to show the hint and allow re-answering."""
    st.session_state.hint_revealed = True
    st.session_state.awaiting_action_after_incorrect = False
    st.session_state.user_answer = ""
    st.session_state.show_answer = False

def reveal_answer():
    """Callback to reveal the answer and move to the next question."""
    st.session_state.show_answer = True
    st.session_state.awaiting_action_after_incorrect = False
    current_question = st.session_state.questions_list[st.session_state.current_question_index]
    st.session_state.incorrect_questions.append(current_question)

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

# The main conditional block to control page flow
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
        st.warning(f"No question data found. Please check your `{os.path.basename(DATA_FILE)}` file.")

elif not st.session_state.questions_list:
    # New Page: Topic Selection
    st.header(f"Select Topics for {st.session_state.event} 📚")
    
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
        st.warning(f"No questions loaded for {st.session_state.event}. Please check your CSV file.")
        st.button("Back to Events", on_click=return_to_event_selection)

else:
    # Practice Mode (Study Mode)
    st.header(f"Practice Mode: {st.session_state.event} ✨")

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
            st.error("❌ Incorrect. Would you like to try again with a hint or reveal the answer?")
            col1, col2 = st.columns(2)
            with col1:
                st.button("Show Hint", use_container_width=True, on_click=show_hint)
            with col2:
                st.button("Reveal Answer", use_container_width=True, on_click=reveal_answer)
        
        # UI for revealed answer after incorrect action
        elif st.session_state.show_answer and st.session_state.last_answer_state == 'incorrect':
            # Display hint only if the user revealed it
            if st.session_state.hint_revealed and 'hint' in question_data and pd.notna(question_data['hint']):
                st.info(f"Hint: {question_data['hint']}")
            
            st.error(f"❌ Incorrect. The correct answer is: **{question_data['answer']}**")
            st.info("Question has been added to cheat sheet for review.")
            if 'explanation' in question_data and pd.notna(question_data['explanation']):
                st.info(f"Explanation: {question_data['explanation']}")
            st.button("Next Question", use_container_width=True, on_click=next_question)
        
        st.markdown("---")

    else:
        # End of Drill screen
        st.header("Drill Complete! 🎉")
        st.write(f"You answered **{st.session_state.score}** out of **{st.session_state.attempted_questions}** questions correctly.")
        
        st.subheader("Cheat Sheet")
        if st.session_state.incorrect_questions:
            # Generate the cheat sheet text for download
            cheat_sheet_text = ""
            for q_data in st.session_state.incorrect_questions:
                phrase = generate_cheat_sheet_phrase(q_data)
                cheat_sheet_text += f"- {phrase}\n\n"
            
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
            st.info("You got all the questions right! No cheat sheet needed.")
        
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
        
        if st.session_state.event and st.button("Back to Events", use_container_width=True, on_click=return_to_event_selection):
            pass
