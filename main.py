from dataclasses import dataclass, asdict, field
from bs4 import BeautifulSoup
import pandas as pd
import requests


MAIN_URL = 'http://hriranytu.hu/'

URLS = [
    'http://hriranytu.hu/blog.html',
    'http://hriranytu.hu/blog2679.html?page=1',
    'http://hriranytu.hu/blog4658.html?page=2',
    'http://hriranytu.hu/blog9ba9.html?page=3',
    'http://hriranytu.hu/blogfdb0.html?page=4',
    'http://hriranytu.hu/blogaf4d.html?page=5',
    'http://hriranytu.hu/blogc575.html?page=6',
    'http://hriranytu.hu/blog235c.html?page=7',
    'http://hriranytu.hu/blogfdfa.html?page=8',
    'http://hriranytu.hu/blog0b08.html?page=9'
]


DATES = {
    'jan': '01',
    'feb': '02',
    'mar': '03',
    '\u00e1pr': '04',
    'm\u00e1j': '05',
    'j\u00fan': '06',
    'j\u00fal': '07',
    'aug': '08',
    'szep': '09',
    'okt': '10',
    'nov': '11',
    'dec': '12'
}


@dataclass
class Blog:
    title: str = None
    image: str = None
    original_link: str = None
    converted_link: str = None
    date: str = None
    tags: str = None
    body: str = None


@dataclass
class BlogList:
    blog_list: list[Blog] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize([asdict(b) for b in self.blog_list], sep='_')


def to_unicode(s):
    # for some reason gives an error even though U+0151 is in latin1 encoding
    if '\u0151' in s:
        return s

    return s.encode('latin1').decode('utf8')


def main():
    writer = pd.ExcelWriter("blogs.xlsx", engine='xlsxwriter')

    blog_list = BlogList()
    for url in URLS:
        html_text = requests.get(url).text
        soup = BeautifulSoup(html_text, 'lxml')

        posts = soup.find_all('div', class_='post')
        for post in posts:
            blog = Blog()

            # title
            blog.title = to_unicode(post.find('div', class_='post-title').text.replace('\n', ''))

            # image
            blog.image = MAIN_URL + post.find("img")["src"]

            # original link
            blog.original_link = post.find('div', class_='post-format').find('a')['href']

            # converted link
            blog.converted_link = '/' + blog.original_link.removesuffix('.html')

            # date
            date = to_unicode(post.find('div', class_='post-meta').find('li').find('span').text).lower()
            for month, numerical in DATES.items():
                date = date.replace(month, numerical)
            date = date.split(' ')
            blog.date = f'{date[2]}-{date[0]}-{date[1]}'

            # tags
            blog.tags = ', '.join([to_unicode(tag.text) for tag in
                                   post.find('div', class_='post-meta').find_all('a', typeof='skos:Concept')])

            # body
            html_text_for_blog = requests.get(MAIN_URL + blog.original_link).text
            blog_soup = BeautifulSoup(html_text_for_blog, 'lxml')
            blog.body = ''.join([
                to_unicode(str(line).strip()) for line in
                blog_soup.find('div', class_='post-body').find('div', class_='field-item even').children
            ])

            # adding blog to blog_list
            blog_list.blog_list.append(blog)

    df = blog_list.dataframe()
    df.to_excel(writer, sheet_name='Blogs', startrow=1, header=False, index=False)

    worksheet = writer.sheets['Blogs']

    (max_row, max_col) = df.shape

    column_settings = []
    for header in df.columns:
        column_settings.append({'header': header})

    worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})

    writer.close()


if __name__ == '__main__':
    main()
