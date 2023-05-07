#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata
import os

#%%
def scrape_data(keyword, number_of_results, start_year, end_year, review_articles=0):
    data = []
    headers=["Title", "Abstract", "Citations", "Link", "AJYP"]
    for page in range(0, number_of_results, 10):
        if start_year == "" and end_year == "":
            url = f"https://scholar.google.com/scholar?start={page}&q={keyword}&hl=en&as_sdt=0,5&as_rr={review_articles}"
        else:
            url = f"https://scholar.google.com/scholar?start={page}&q={keyword}&hl=en&as_sdt=0,5&as_ylo={start_year}&as_yhi={end_year}&as_rr={review_articles}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find(id="gs_res_ccl")
        if main_content:
            articles = main_content.find_all("div", class_="gs_ri")
            for article in articles:
                title = article.find("h3", class_="gs_rt").text
                abstract = article.find("div", class_="gs_rs").text
                ajyp = article.find("div", class_="gs_a").text
                link_element = article.find("h3", class_="gs_rt").find("a")
                link = link_element["href"] if link_element else ""
                
                # Get the citation count
                citation_count = 0
                citation_count_section = article.find("div", class_="gs_fl")
                if citation_count_section:
                    for citation_link in citation_count_section.find_all("a"):
                            if citation_link.text.startswith("Cited by"):
                                citation_count = citation_link.text.replace("Cited by", "").strip()
                                break
                try:
                    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('utf-8')
                    abstract = unicodedata.normalize('NFKD', abstract).encode('ascii', 'ignore').decode('utf-8')
                    ajyp = unicodedata.normalize('NFKD', ajyp).encode('ascii', 'ignore').decode('utf-8')
                    data.append([title, abstract, citation_count, link, ajyp])
                except:
                    data.append([title, abstract, citation_count, link, ajyp])
    df = pd.DataFrame(data, columns=headers)
    df.index.name = 'Rank'
    df["Citations"]= df["Citations"].astype('Int64')       
    return df

#%%
def extract_info(df, column_name):
    result=[]
    year_regex = r"\b\d{4}\b"
    for text in df[column_name]:
        parts = text.split("- ")
        if len(parts) == 3:
            author = parts[0].strip()
            publisher = parts[2].strip()

            try:
                year = re.findall(year_regex, parts[1])[-1]
                journal = parts[1][::-1].replace(year[::-1], ""[::-1],1)[::-1].strip().rstrip(",")
            except IndexError:
                year = ""
                journal = parts[1]

        if len(parts) == 2:
            author = parts[0].strip()
            try:
                year = re.findall(year_regex, parts[1])[-1]
                journal = parts[1][::-1].replace(year[::-1], ""[::-1],1)[::-1].strip().rstrip(",")
                publisher = ""
            except IndexError:
                year = ""
                journal = ""
                publisher = parts[1]
        result.append({'Author': author, 'Journal': journal, 'Publisher': publisher, 'Year': (year)})
    df = pd.DataFrame(result)
    df["Year"] = pd.DatetimeIndex(df["Year"]).year.astype('Int64')
    return df

#%%
kw= input("Enter keyword: ")
num_of_results = input("Enter number of results (or press enter for default value 50): ") or 50
start_year = input("Enter start year: ")
if start_year != "":
    int(start_year)
end_year = input("Enter end year: ")
if end_year != "":
    int(end_year)
review_articles = int(input("Enter 0 for non-review articles only or 1 for review articles only (or press enter for default of 0): ") or 0)

df = scrape_data(kw, number_of_results=int(num_of_results), start_year=start_year, end_year=end_year, review_articles=review_articles)

df.head()

#%%
try:
    df = pd.concat([df,extract_info(df,"AJYP")],axis=1)
except:
    pass
df.head()
#%%
try:
    df['Cit/Year']=(df['Citations']/(df['Year'].max() + 1 - df['Year'])).round(0).astype('Int64')
except:
    pass
df.head()
# %%
try:
    ax = df['Year'].value_counts().sort_index().plot(kind='bar', figsize=(10, 6))
    ax.set_xlabel('Year')
    ax.set_ylabel('Publications')
    ax.set_title('Publications Per Year')
    filename = 'publication_per_year.png'
    # Check if the file already exists
    while os.path.exists(filename):
        user_input = input(f"The file '{filename}' already exists. Enter 'y' to overwrite or enter a new filename: ")
        if user_input.lower() == 'y':
            break
        else:
            filename = user_input

    # Save the plot as an image file
    fig = ax.get_figure()
    fig.savefig(filename)

except:
    pass
#%%
try:
    df = df.sort_values(by=input('Sort by preferred columns i.e.(Title, Author, Year or Cit/Year)\n Dafault is by "Citations"'), ascending=False)
except Exception as e:
    print('Column name to be sorted not found. Sorting by the number of citations...')
    df = df.sort_values(by='Citations', ascending=False)

#%%
columns=["Author","Title","Citations","Year", 'Cit/Year',"Abstract","Link","Journal","Publisher","AJYP"]

try:
    df[columns].to_csv(f"{kw}_gs.csv")
except:
    try:
        df[columns].to_csv("file_gs.csv")
    except:
        try:
            df.to_csv(f"{kw}_gs.csv")
        except:
            df.to_csv("file_gs.csv")

# %%
