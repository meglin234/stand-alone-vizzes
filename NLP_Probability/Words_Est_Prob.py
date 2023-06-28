import pandas as pd
import time



##### DATA EXTRACTION #####
###########################


from lxml import html
from selenium import webdriver
from bs4 import BeautifulSoup as bs4


## Create a data frame 

# read in pmcids
df = pd.read_csv('PMIDs/pmc_edu_psyc.txt', sep = ' ', 
                 header = None, 
                 names = ['pmcid', 'date', 'title', 'body'])

# make column types objects 
df = df.astype(object)

# select 200 entries at a time  
df = df.iloc[:200]

# reset the index for the loop to work 
df = df.reset_index(drop=True)


## download the Chrome driver
#wget https://chromedriver.storage.googleapis.com/110.0.5481.77/chromedriver_linux64.zip && unzip chromedriver_linux64.zip




## Use Selenium to get the html for each entry 
pubmed_url = "https://www.ncbi.nlm.nih.gov/pmc/articles/{}"

# loop through all the entries
for row in range(len(df)):
    pubmed_article = pubmed_url.format(df.iloc[row,0])

    # set the path to the Chrome driver
    driver_path = "chromedriver"

    # create an instance of the Chrome driver
    driver = webdriver.Chrome(driver_path)

    # get the HTML from the webpage
    driver.get(pubmed_article)
    time.sleep(1)

    with open('preprints_w_content.html', 'w') as html_out:
        html_out.write(driver.page_source)

    html_source = driver.page_source
    driver.close()
    
    
    soup = bs4(html_source, "lxml")

    # use soup to find all the tags we want 
    date = soup.find_all("span", {"class": "fm-vol-iss-date"})
    title = soup.find_all('h1')
    articles = soup.find_all("div", {"class": "tsec sec"})
    
    # get the text form each tag
    date = [a.text.strip() for a in date]                      
    title = [a.text.strip() for a in title]
    body = [a.text.strip() for a in articles]

    
    #put the extracted data to the data frame 
    df.at[row, 'date'] = date                   
    df.at[row, 'title'] = title
    df.at[row, 'body'] = body




# subset columns
df = df[['pmcid', 'date', 'title', 'body']]

# save 
df.to_csv('all_pubmed_articles.csv')



##### PREPROCESSING #####
#########################


import re
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import string

from tqdm import tqdm
tqdm.pandas()

punctuation = list(string.punctuation)
STOP_WORDS.update(punctuation)

NLP = spacy.load('en_core_web_sm', disable=['parser', 'ner'])

# remove probabilistic stopwords from spacy's set
NLP.Defaults.stop_words -= {'always', 'often', 'never'}




# read in saved data 
data = pd.read_csv('data/all_pubmed_articles.csv')

# subset columns
df = data[['pmcid', 'date', 'body']]

# subset rows 
df = df[:1140]

# extract the year from the date
df['date'] = df.date.str.extract(r'(\d{4})')



# create a new df
df_split = pd.DataFrame(columns = ['pmcid', 'year', 'part', 'text'])
extractor = r"(Go to:.*?)(?=Go to:)"

# extract body sections of each article
for i in range(len(df)):
    body = df.loc[i, 'body']
    captured = re.findall(extractor, body, flags = re.MULTILINE)
    
    # split the body part title from the text 
    for item in captured: 
        # capture up till capital letter immeditally precedied by lowercase letter (Go to:Introduction sectionThere)
        match = r"(Go to.*?[a-z](?=[A-Z]))"
        # replace the parts tag with nothing to isolate the text 
        text = re.sub(match, '', item, flags = re.MULTILINE)
        
        try: # isolate the body part title if it exists 
            parts = re.search(match, item, flags = re.MULTILINE).group()  
            parts = parts.split(':')[1]
        except AttributeError: # otherwise set the title to blank
            parts = ''
            
        
        # add the article parts to the new data frame using concat because pandas removed .append()
        values = {'pmcid' : df.loc[i, 'pmcid'], 'year' : df.loc[i, 'date'], 'part' : parts, 'text' : text}
        df_split = pd.concat([df_split, pd.DataFrame.from_records([values])], ignore_index = True)
        


# get a list of the body text lemmas with punctuation and stopwords removed
df_split['tokens'] = df_split['text'].progress_apply(
    lambda x: [x.lemma_.lower() for x in NLP(x) if x.lemma_.lower() not in STOP_WORDS])

# get a list of the part lemmas with punctuation and stopwords removed
df_split['part_token'] = df_split['part'].progress_apply(
    lambda x: [x.lemma_.lower() for x in NLP(x) if x.lemma_.lower() not in STOP_WORDS])


# so you don't have to wait for the tokens if you mess up 
df_new = df_split


# define the parts to normalize 
parts = ['abstract', 'introduction', 'method', 'result', 'discussion', 'conclu', 'future', 
         'limitation', 'footnote', 'background', 'analysis', ]



# attempt to normalize the parts 
expression = r"{}"

for i in range(len(df_new)):
    string = df_new.loc[i, 'part_token']
    for part in parts:
        exp = expression.format(part)
        for item in string:
            if re.search(exp, item):
                df_new.loc[i, 'part'] = exp



# unwind the data on the tokens
df_split = df_split[['pmcid', 'year', 'part', 'tokens']]
df_tokens = (df_split.explode('tokens'))


# define the key probabilistic terms 
words = 'always usually certainly likely frequently probably often maybe possibly probability unlikely rarely never'

# lemmatize the key words to match the lemmatized tokens
key_words = [x.lemma_.lower() for x in NLP(words) if x.lemma_.lower() not in STOP_WORDS]

# subset the tokens that are probabalistic 
df_tokens = df_tokens.loc[df_tokens['tokens'].isin(key_words)]



##### FREEQUENCIES #####
########################

import matplotlib.pyplot as plt
import seaborn as sns


# group by PMCID and part 
term_frequency = (df_tokens
                  .groupby(by=['pmcid', 'part', 'tokens'])
                  .agg({'tokens': 'count'})
                  .rename(columns={'tokens': 'term_frequency'})
                  .reset_index()
                  .rename(columns={'title_tokens': 'term'})
                 )


# term count by pmcid 
term_frequency['pmcid'].value_counts()


# term count by tem 
term_frequency['tokens'].value_counts()

# graph
fig, ax = plt.subplots(figsize=(5, 7))
sns.countplot(y = 'tokens', 
              data = term_frequency, 
              order = term_frequency['tokens'].value_counts().index, 
              ax = ax,
              color = 'pink').set(xlabel = 'Word Count', ylabel = '')
sns.despine()


