import streamlit as st
import requests
from datetime import time
import pandas as pd
import folium
import numpy as np


# Streamlit app starts here

st.set_page_config(
    page_title='Recipes by Sol and Ester',
    page_icon='🍲',
    layout='wide'
)

# Set the RapidAPI key
api_key = ''

st.header('Recipe Explorer')


# Function to create a colored title
@st.cache_data
def colored_title(text, color):
    return f"<span style='color:{color}; font-size:32px'>{text}</span>"


st.markdown(
    colored_title('All Recipes in One Place', 'pink'), unsafe_allow_html=True)
# Define image URLs and corresponding headers
image_data = [
    {
        'url': 'https://www.washingtonpost.com/wp-apps/imrs.php?src=https://arc-anglerfish-washpost-prod-washpost.s3.amazonaws.com/public/63O2DBTTTEI6VKN5T6FVSMYA2A.jpg&w=860'},
    # Add more images as needed
]

# Add images and headers to the center of the page
for item in image_data:
    st.image(item['url'], width=380)  # Adjust the width as needed


# Function to fetch recipe data from the Spoonacular API by name
@st.cache_data
def search_recipe_by_name(query):
    url = 'https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/complexSearch'

    # Convert query to string in case it's not
    query_string = str(query)

    querystring = {'query': query_string,
                   'type': 'main course',
                   'instructionsRequired': 'true',
                   'fillIngredients': 'true',
                   'addRecipeInformation': 'true',
                   'sort': 'calories',
                   'sortDirection': 'asc'}

    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
    }

    response = requests.get(url, headers=headers, params=querystring)
    return response.json()


# Function to fetch recipes from the Spoonacular API by cuisine
@st.cache_data
def get_recipes_by_cuisine(cuisine_type):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/random"
    querystring = {"tags": f"{cuisine_type}", "number": "1"}

    headers = {
        "X-RapidAPI-Key": "1e2736ff9bmsh20f49c63b4f9245p18309djsn5b02aaf9d2a3",
        "X-RapidAPI-Host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    return response.json()


# Function to create a cuisine radio button
@st.cache_data
def select_cuisine():
    cuisines = ['Italian', 'Mediterranean', 'Indian', 'Chinese', 'Mexican']
    return cuisines


# Function to display bar graph widget using recipeID
@st.cache_data
def display_recipe_nutrition_chart(recipe_id):
    url = f'https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{recipe_id}/nutritionWidget.png'

    headers = {
        'X-RapidAPI-Key': '1e2736ff9bmsh20f49c63b4f9245p18309djsn5b02aaf9d2a3',
        'X-RapidAPI-Host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
    }

    response = requests.get(url, headers=headers)
    st.subheader('Nutrition Chart')
    st.image(response.content, use_column_width=True)


# Function to display recipe ingredients by id
@st.cache_data
def display_recipe_ingredients(recipe_id):
    url = f'https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{recipe_id}/ingredientWidget.json'

    headers = {
        "X-RapidAPI-Key": "1e2736ff9bmsh20f49c63b4f9245p18309djsn5b02aaf9d2a3",
        "X-RapidAPI-Host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    return response.json()


# Search option
search_option = st.sidebar.selectbox('Search Option:', ['Search by Name', 'Search by Cuisine Type'])

if search_option == 'Search by Name':
    # Recipe by Name
    recipe_name = st.text_input('Enter Recipe Name:', key='recipe_name_input')

    # Initialize session state for recipe data if it doesn't exist
    if 'recipe_data' not in st.session_state:
        st.session_state.recipe_data = None

    if st.button('Search'):
        # Fetch and store recipe data in session state
        st.session_state.recipe_data = search_recipe_by_name(recipe_name)

    # Check if recipe data is available in session state
    if st.session_state.recipe_data and 'results' in st.session_state.recipe_data:
        # Generate list of recipe names
        recipe_names = [recipe['title'] for recipe in st.session_state.recipe_data['results']]
        recipe_names.insert(0, '')

        # Create a selectbox with the recipe names
        recipe_selected = st.selectbox('Select a recipe', options=recipe_names)

        if recipe_selected:
            for recipe in st.session_state.recipe_data['results']:
                if recipe['title'] == recipe_selected:
                    st.success(f'You have successfully chosen the recipe {recipe_selected}', icon='✅')
                    recipe_selected_id = recipe['id']

                    recipe_ingredients = display_recipe_ingredients(recipe_selected_id)

                    # Convert recipe ingredients to a flattened DataFrame
                    recipe_df = pd.json_normalize(recipe_ingredients['ingredients'], sep='_')

                    # Remove the 'image' column
                    recipe_df = recipe_df.drop(columns='image', errors='ignore')
                    recipe_df = recipe_df.drop(columns='amount_us_value', errors='ignore')
                    recipe_df = recipe_df.drop(columns='amount_us_unit', errors='ignore')

                    # Rename the columns
                    recipe_df = recipe_df.rename(columns={
                        'name': 'Ingredient',
                        'amount_metric_value': 'Amount',
                        'amount_metric_unit': 'Unit'
                    })

                    # Display the DataFrame with customized column names
                    st.subheader("Ingredient List")
                    st.table(recipe_df)

                    recipe_ingredients_dict = [
                        {'name': ingredient['name'], 'amount': ingredient['amount']['metric']['value'],
                         'unit': ingredient['amount']['metric']['unit']} for ingredient in
                        recipe_ingredients['ingredients']]

                    # Create a list of formatted ingredient strings
                    ingredient_options = [f"{ingredient['name']} {ingredient['amount']} {ingredient['unit']}" for
                                          ingredient in recipe_ingredients_dict]

                    # Display the multi-select box
                    selected_ingredients = st.multiselect("Select the Ingredients You Already Own For This Recipe:",
                                                          options=ingredient_options)

                    col1, col2 = st.columns(2)

                    # You can process 'selected_ingredients' as needed
                    with col1:
                        st.subheader('Allergens:')
                        peanuts_allergen = st.checkbox('Contains Peanuts')
                        milk_allergen = st.checkbox('Contains Milk')
                        # Display feedback and message boxes
                        if peanuts_allergen:
                            st.warning('Warning: This recipe contains peanuts!')
                        if milk_allergen:
                            st.info('Information: This recipe contains milk.')

                    with col2:
                        appointment = st.slider(
                            "You can schedule your cooking time here:",
                            value=(time(11, 30), time(12, 45))
                        )

                        formatted_start_time = appointment[0].strftime("%H:%M")
                        formatted_end_time = appointment[1].strftime("%H:%M")

                        st.write(f"You're scheduled from {formatted_start_time} to {formatted_end_time}")

                    display_recipe_nutrition_chart(recipe_selected_id)

        else:
            st.error('You selected a blank recipe, please select a valid recipe!', icon="🚨")

elif search_option == "Search by Cuisine Type":
    # Recipe by Cuisine

    selected_cuisine = st.radio('Select Cuisine:', select_cuisine())

    if selected_cuisine:
        st.session_state.recipe_data = get_recipes_by_cuisine(selected_cuisine.lower())
        col1, col2, col3 = st.columns(3)
        with col1:
            st.title(st.session_state.recipe_data['recipes'][0]['title'])
        with col2:
            if selected_cuisine == "Indian":
                st.image('https://spoonacular.com/recipeImages/716364-556x370.jpg',
                         caption=st.session_state.recipe_data['recipes'][0]['title'], output_format='auto')
            else:
                st.image(st.session_state.recipe_data['recipes'][0]['image'],
                         caption=st.session_state.recipe_data['recipes'][0]['title'], output_format='auto')
        with col3:
            st.session_state.recipe_data['recipes'][0]['instructions']
    if st.session_state.recipe_data:
        print("test")

        #Italian

        steps = len(st.session_state.recipe_data['recipes'][0]['analyzedInstructions'][0]['steps'])+1
        chartPercentageListArr = [i*10 for i in range(steps)]
        chartListArr = [i for i in range(steps)]
        chart_data = pd.DataFrame(
            {
                "Number of Steps":chartListArr,
                "% To Recipe Completion":chartPercentageListArr
        }
        )
        len(st.session_state.recipe_data['recipes'][0]['analyzedInstructions'])
        print(len(st.session_state.recipe_data['recipes'][0]['analyzedInstructions'][0]['steps']))
        st.line_chart(chart_data, x = "Number of Steps", y = "% To Recipe Completion")



        # Generate list of recipe names
       # recipe_names = [recipe['title'] for recipe in st.session_state.recipe_data['results']]
       # recipe_names.insert(0, '')

        # Display recipes on the map
        st.subheader(f'Map of {selected_cuisine.lower()} Region')

        # Set the center and zoom level based on the cuisine
        if selected_cuisine == 'Italian':
            center = [41.8719, 12.5674]  # Italy
            zoom_level = 6
        elif selected_cuisine == 'Mediterranean':
            center = [35.8617, 14.3822]  # Mediterranean
            zoom_level = 4
        elif selected_cuisine == 'Indian':
            center = [20.5937, 78.9629]  # India
            zoom_level = 4
        elif selected_cuisine == 'Chinese':
            center = [35.8617, 104.1954]  # China
            zoom_level = 4
        elif selected_cuisine == 'Mexican':
            center = [23.6345, -102.5528]  # Mexico
            zoom_level = 5


        # Create a folium map centered at the specified location with a custom zoom level
        m = folium.Map(location=center, zoom_start=zoom_level)

        # Display the map using st.components
        st.components.v1.html(m._repr_html_(), height=600)
