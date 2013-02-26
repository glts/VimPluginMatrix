import datetime, json, re, sys
import bs4
import jinja2
import markdown
import requests

DATABASE = 'plugins.json'
TEMPLATE = 'template.html'
OUTPUT   = 'index.html'

def get_description_for_type(type):
    if type == 'completion':
        return "completion: plugins dealing with automatic or triggered completion and/or code templating (snippets)"
    elif type == 'plugin management':
        return "plugin management: plugins providing ways of managing Vim plugins"
    elif type == 'buffer management':
        return "buffer management: plugins helping with finding and navigating buffers, windows, files, etc."
    elif type == 'framework':
        return "framework: plugins providing functionality for other plugins, not for the end user directly"
    elif type == 'utility':
        return "utility: plugins modifying, extending, or in a very general way building on top of core Vim functionality"
    elif type == 'add-on':
        return "add-on: plugins adding new functionality unrelated to core Vim"
    else:
        return ""

TODAY          = datetime.date.today()
ONE_MONTH_AGO  = TODAY - datetime.timedelta(days=30)
TWO_MONTHS_AGO = TODAY - datetime.timedelta(days=60)
SIX_MONTHS_AGO = TODAY - datetime.timedelta(days=180)
ONE_YEAR_AGO   = TODAY - datetime.timedelta(days=365)
def get_recentness_for_date(date):
    if date > ONE_MONTH_AGO:
        return (1, "Last updated less than a month ago")
    elif date > TWO_MONTHS_AGO:
        return (2, "Last updated less than two months ago")
    elif date > SIX_MONTHS_AGO:
        return (3, "Last updated less than half a year ago")
    elif date > ONE_YEAR_AGO:
        return (4, "Last updated less than a year ago")
    else:
        return (5, "Last updated more than a year ago")

def add_vim_org_data(plugins):
    vim_org_plugins = [ p for p in plugins if p['vim_org'] ]
    print("Fetching vim.org data for", len(vim_org_plugins), "plugins")

    for plugin in vim_org_plugins:
        print(plugin['vim_org']['script_id'], ": ", plugin['name'], sep='')
        try:
            data = retrieve_vim_org_data(plugin['vim_org']['script_id'])
            plugin['vim_org']['rating']  = data[0]
            plugin['vim_org']['updated'] = data[1]
        except Exception as e:
            print('... failed!', e)

def retrieve_vim_org_data(script_id):
    url = 'http://www.vim.org/scripts/script.php'
    params = { 'script_id': script_id }
    headers = {'user-agent': "Script by glts, see https://github.com/glts/VimPluginMatrix"}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    soup = bs4.BeautifulSoup(response.text)
    main_div = soup.find('span', class_='txth1').parent

    # Find the script karma table and extract rating
    karma = main_div.table.find_all('td')[1].get_text()
    rating = re.search(r'Rating (\d+)/\d+', karma).group(1)

    # Find the script versions table and extract latest date
    row1 = main_div.find_all('p')[-1].table.find_all('tr', recursive=False)[1]
    datestr = row1.find_all('td')[2].get_text()
    updated = datetime.datetime.strptime(datestr, '%Y-%m-%d').date()
    return (rating, updated)

def add_github_data(plugins):
    github_plugins = [ p for p in plugins if p['github'] ]
    print("Fetching Github data for", len(github_plugins), "plugins")

    for plugin in github_plugins:
        print(plugin['github']['repo'], ": ", plugin['name'], sep='')
        try:
            data = retrieve_github_data(plugin['github']['repo'])
            plugin['github']['rating']  = data[0]
            plugin['github']['updated'] = data[1]
        except Exception as e:
            print('... failed!', e)

def retrieve_github_data(repo):
    url = 'https://api.github.com/repos/' + repo
    auth = (sys.argv[1], sys.argv[2])
    headers = {'user-agent': "Script by glts, see https://github.com/glts/VimPluginMatrix"}

    response = requests.get(url, auth=auth, headers=headers)
    response.raise_for_status()

    repodata = json.loads(response.text)
    stars = repodata['watchers_count']
    updated = datetime.datetime.strptime(repodata['pushed_at'], '%Y-%m-%dT%H:%M:%SZ').date()
    return (stars, updated)

def main():
    """
    Loads the JSON plugin database, decorates the plugins with data fetched
    from vim.org and Github, renders the template and writes it to index.html.
    """
    with open(DATABASE, 'r', encoding="utf-8") as dbfile:
        plugins = json.load(dbfile)

    add_vim_org_data(plugins)
    add_github_data(plugins)

    env = jinja2.Environment()
    env.globals['get_description_for_type'] = get_description_for_type
    env.globals['get_recentness_for_date'] = get_recentness_for_date
    env.filters['markdown'] = markdown.markdown

    with open(TEMPLATE, 'r', encoding="utf-8") as tplfile:
        template = env.from_string(tplfile.read())

    types = set([p['type'] for p in plugins])
    with open(OUTPUT, 'w', encoding="utf-8") as outfile:
        outfile.write(template.render(plugins=plugins, types=types, date=TODAY))

if len(sys.argv) != 3:
    print("Usage:", sys.argv[0], "<githubuser> <githubpass>")
    sys.exit(1)

main()
