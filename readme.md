# ChatHarvard

A specialized academic assistant for Harvard students to navigate course selection, requirements, and get personalized recommendations based on Q Guide data.

## Overview

ChatHarvard analyzes course data from Harvard's Q Guide, concentration requirements, and your personal academic profile to provide tailored recommendations and answers to your questions about courses and requirements.

## Features

- **Smart Course Search**: Find courses based on department, level, term, and other criteria
- **Personalized Recommendations**: Get course recommendations based on your concentration, courses taken, and preferences
- **Q Guide Analysis**: Access data on course ratings, workload, and student comments
- **Concentration Requirements**: Get information about your concentration requirements
- **Conversational Interface**: Chat naturally to ask questions about courses and requirements

## Setup and Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd chatHarvard
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Place your data files in the project directory:
   - subjects_rows.csv
   - courses_rows.csv
   - q_reports_rows_1.csv
   - q_reports_rows_2.csv

4. Run the application:
   ```
   streamlit run app.py
   ```

5. Enter your Anthropic API key when prompted

## Project Structure

- **app.py**: Main application interface and Streamlit setup
- **database.py**: Database module for course data management
- **query_processor.py**: Analyzes user queries to understand intent
- **course_finder.py**: Finds relevant courses based on query criteria
- **course_recommender.py**: Provides personalized course recommendations
- **context_builder.py**: Creates rich context for the LLM responses

## Usage Examples

Here are some example questions you can ask ChatHarvard:

- "What 130s level Math courses are offered in the Fall?"
- "I need to take a course with less than 10 hours of work per week. What do you recommend?"
- "What are the requirements for a Mathematics concentration?"
- "I'm a CS major. What courses should I take after CS50?"
- "What's the easiest 100-level Economics course?"
- "Tell me about Math 136. What are the student comments like?"

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built using Claude API from Anthropic
- Powered by Streamlit for the web interface
- Uses Harvard Q Guide data for course information