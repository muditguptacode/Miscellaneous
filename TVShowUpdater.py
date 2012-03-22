import os, re, urllib, urllib2, string, pickle, sys
import _winreg as reg
import subprocess, optparse

verbose = False

def main():
        print_matches = False
        update_available = False
        local_db_store = False
        
        search_paths = get_path()
        search_paths.append(os.path.dirname(sys.argv[0]))
        search_paths.append(r'D:\Downloads\Torrents')
        
        print "\nHold on. Let me guess what you watch..\n"
        local_list = find_local_show_list(search_paths)
        if not len(local_list):
            print "Sorry, I can't seem to think of any TV shows that you watch. Bye!"
            if verbose:
                raw_input()
            sys.exit(0)
        print_local_show_list(local_list)
        
        print "\nSit tight, I'm doing some cool stuff.."
        remote_list, fixed_remote_list = find_remote_show_list(local_db_store)
        
        matched_list = match_local_and_remote_list(local_list, remote_list, fixed_remote_list)
        if len(matched_list) < len(local_list):
            print "\nI can only help you with the ones below. You're on your own with the rest. \n"
            print_matches = True
        final_list = get_final_show_list(local_list, matched_list, print_matches)    
        print   
        
        updates_list = find_show_updates(final_list)
        mark_shows_to_update(updates_list, final_list)
        
        for show in updates_list:
            if updates_list[show][0].has_key("update_available"):
                print "\n\nHere's all the new stuff that you don't have:"
                update_available = True
                break; 
        
        if not update_available:         
                print "\nYou're upto date already. Go do something else.\nBye!\n"
                if verbose:
                    raw_input()
                sys.exit(0)

        print_shows_to_update(updates_list)

        if verbose:
            print "\nGo on, hit any key. I'll automatically download them for you.\nOr press Ctrl+C, if you dare."
            raw_input()
            
        torrent_cmd = get_torrent_cmd()
        start_torrent_application(torrent_cmd, updates_list)
        
        print "\nIts done. Now, go do something actually productive for a change. Bye! \n"
        if verbose:
            raw_input()
        sys.exit(0)

def get_path():
    path = []
    
    home_drive = os.getenv("HOMEDRIVE")
    home_path = home_drive + "\\" + os.getenv("HOMEPATH")
    
    temp_path = home_path + "\\Downloads"
    if os.path.exists(temp_path): path.append(temp_path)
    temp_path = home_path + "\\My Documents\\Downloads"
    if os.path.exists(temp_path): path.append(temp_path)
    temp_path = home_path + "\\Documents\\Downloads"
    if os.path.exists(temp_path): path.append(temp_path)
    temp_path = home_path + "\\Videos"
    if os.path.exists(temp_path): path.append(temp_path)
    temp_path = home_path + "\\My Documents\\My Videos"
    if os.path.exists(temp_path): path.append(temp_path)
    return path


def find_local_show_list(paths):
    show_list = {}
    regex = re.compile(r'(.*?)((S *?(\d{1,2}).*?E *?(\d{1,2}))|(Season *?(\d{1,2}).*?Episode *?((\d{1,2})))|( (\d)(\d{2}) )).*(.mp4|.avi|.mkv|.flv|.txt)$', re.IGNORECASE)
    for path in paths:
        try:
            for path, dirs, files in os.walk(path):
                for file in files:
                    show = regex.match(file)
                    if show:
                        show_name = show.group(1).replace('.', ' ').strip().capitalize()
                        if not show.group(1):
                            continue
                        elif show.group(7) and show.group(8):
                            show_season, show_episode = show.group(7), show.group(8)
                        elif show.group(4) and show.group(5):
                            show_season, show_episode = show.group(4), show.group(5)
                        else:
                            show_season, show_episode = show.group(11), show.group(12)
                        if show_name in show_list:
                            if int(show_season) > int(show_list[show_name][0]):
                                show_list[show_name] = show_season, show_episode
                            elif int(show_episode) > int(show_list[show_name][1]):
                                    show_list[show_name] = (show_list[show_name][0], show_episode)
                        else:
                            show_list[show_name] = show_season, show_episode
        except Exception as ex:
            print "Warning:", ex.message, "\n\n"
            pass
    return show_list

def print_local_show_list(show_list):
    for show in show_list:
        print show, "- Upto S" + str(show_list[show][0]) + "E" + str(show_list[show][1])

def find_remote_show_list(local_db_store):
    if local_db_store and os.path.exists(os.path.join(os.path.dirname(__file__),"ShowListDB.pkd")):
        shows_file = open(os.path.join(os.path.dirname(__file__),"ShowListDB.pkd"), 'r')
        remote_show_list_raw = pickle.load(shows_file)
        shows_file.close()
        del(shows_file)
    else:
        url = r"http://www.eztv.it"
        try: fetched_data = urllib2.urlopen(url, timeout=30).read()
        except urllib2.URLError as e: 
            print "Sorry, your internet's not cool enough. Bye!"
            if verbose: raw_input()
            sys.exit(1)
        remote_show_list_raw = re.search(r'<select name="SearchString">(.*?)</select>', fetched_data, re.DOTALL).group(1)
        remote_show_list_raw = re.findall(r'<option value="(.+?)">(.*?)</option>', ''.join(remote_show_list_raw))
        if local_db_store:
            try:
                shows_file = open(os.path.join(os.path.dirname(__file__),"ShowListDB.pkd"), 'w')
                pickle.dump(remote_show_list_raw, shows_file)
                shows_file.close()
            except:
                pass
                
    remote_show_list = []
    for show in remote_show_list_raw:
        remote_show_list.append(':'.join(show))
    remote_show_list = '\n'.join(remote_show_list)
    # Fix the suffixed 'The' in some shows by prefixing it and re-form a fixed list
    fixed_show_list = re.sub(r':(.*), The',r':The \1',remote_show_list)
    return remote_show_list, fixed_show_list
    
def match_local_and_remote_list(local_show_list, remote_show_list, fixed_show_list):
    matched_list = {}
    for show in local_show_list:
        regex = re.compile(r'(.*?):('+show + r')\n', re.I)
        res = regex.search(remote_show_list)
        if res: show_name = res.group(2).capitalize(); matched_list[show_name] = res.group(1)
        else:
            res = regex.search(fixed_show_list)
            if (res):
                show_name = res
                show_name = res.group(2).capitalize()
                matched_list[show_name] = res.group(1)
            else: 
                show_modified = re.sub(r'(.*?) +\d{2,4}$',r'\1',show)
                show_modified = re.sub(r'^\d{2,4} +(.*)', r'\1', show_modified)
                res = re.search(r'(.*?):(.*'+show_modified+r'.*)', remote_show_list, re.IGNORECASE)
                if res: 
                    matched_list[show_modified] = res.group(1)
                    local_show_list[show_modified] = local_show_list[show]
                    del(local_show_list[show])
                else: 
                    res = re.findall(r'(.*?):(.*'+show+r'.*)', remote_show_list, re.IGNORECASE)
                    if res: matched_list[show] = res
    return matched_list
    
def get_final_show_list(show_list, matched_list, print_matches):
    final_list = {}
    for show in matched_list:
        show_value = matched_list[show]
        if not type(show_value) is list:
            if (print_matches): print show
            # Just take this list as final for now.
            # TODO: Fix ambiguities and selective updates with prompts and then generate final list.
            final_list[show] = (show_value, show_list[show][0], show_list[show][1]) 
    
    return final_list
        
def find_show_updates(final_list):
    updates_list = {}
    url = r"http://www.eztv.it/shows/"
    regex = re.compile(r'.*?epinfo.*?>(.*?((S(\d{2})E(\d{2}))|( (\d{1,2})x(\d{1,2}) )).*?)</a>.*?(magnet:.*?)"', re.DOTALL | re.IGNORECASE)
    for show in final_list:
        try:
            print "Investigating", str(show), "..", 
            fetched_show_data = ""
            try:
                fetched_show_data = urllib2.urlopen(url + final_list[show][0] + r"/", timeout=15).read()
            except urllib2.URLError:
                try:
                    fetched_show_data = urllib2.urlopen(url + final_list[show][0] + r"/", timeout=30).read()
                except urllib2.URLError: 
                    print "Skipped. your internet's not cool enough."
                    continue
            if fetched_show_data:
                #print "Done. Parsing data..",
                show_data = regex.findall(fetched_show_data)
                updates_list[show] = {}
                for index, data in enumerate(show_data):
                    updates_list[show][index] = { "info" : show_data[index][0], "season" : int(show_data[index][3] + show_data[index][6]), "episode" : int(show_data[index][4] + show_data[index][7]), "link" : show_data[index][8], "marked_for_update": False }
                air_data = re.search(r'.*show_info_airs_status.*?>.*?<b>(.*?)</b>.*?<b>(.*?)</b>', fetched_show_data, re.IGNORECASE | re.DOTALL)
                print "\b" * (len(show) + 18) + show + " - " + "Status: %s, Airs: %s, Latest: S%sE%s" % (air_data.group(2), air_data.group(1), updates_list[show][0]["season"], updates_list[show][0]["episode"] )
            else:
                print "Skipped. your internet's not cool enough."
        except KeyboardInterrupt:
            print "Skipped"
            continue;
    return updates_list

def mark_shows_to_update(updates_list, final_list):
    regex = re.compile(r'720p|1080p', re.IGNORECASE)
    for show in updates_list: 
        for episode in updates_list[show].items():
            if not regex.search(episode[1]["info"]):
                if int(episode[1]["season"]) > int(final_list[show][1]):
                        updates_list[show][episode[0]]["marked_for_update"] = True
                        updates_list[show][0]["update_available"] = 1
                if int(episode[1]["season"]) == int(final_list[show][1]):
                    if int(episode[1]["episode"]) > int(final_list[show][2]):
                        updates_list[show][episode[0]]["marked_for_update"] = True
                        updates_list[show][0]["update_available"] = 1
    return updates_list                    

def print_shows_to_update(updates_list):
    for show in updates_list:
        if updates_list[show][0].has_key("update_available"):
            print "\n" + str(show), ":"
            prev_ep = 0
            for episode in updates_list[show].items():
                if updates_list[show][episode[0]]["marked_for_update"] == True:
                    if updates_list[show][episode[0]]["episode"] == prev_ep: continue
                    prev_ep = episode[1]["episode"]
                    print "S" + str(episode[1]["season"]) + "E" + str(prev_ep)

def get_torrent_cmd():
    local_reg = reg.ConnectRegistry(None, reg.HKEY_CURRENT_USER)
    dotext_key = reg.OpenKey(local_reg, r'SOFTWARE\Classes\.torrent')
    name, value, type = reg.EnumValue(dotext_key, 0)
    reg.CloseKey(dotext_key)
    location_key = reg.OpenKey(local_reg, r'SOFTWARE\Classes\\' + value + r'\Shell\Open\Command')
    name, value, type = reg.EnumValue(location_key, 0)
    return value

def start_torrent_application(path, updates_list):
    for show in updates_list:
        for episode in updates_list[show].items():
            if updates_list[show][episode[0]]["marked_for_update"] == True:
                subprocess.Popen(string.replace(path, '%1', episode[1]["link"]))

if __name__ == "__main__":

    os.system("title TVShow Updater")
    p = optparse.OptionParser()
    p.add_option('--quiet', '-q', dest='verbose', action='store_false') 
    options, arguments = p.parse_args()
    verbose = options.verbose
    try:
        main()
    except KeyboardInterrupt:
        print "\n\nBye!\n"
    except Exception as ex:
        print "Error:", ex.message
        if verbose: raw_input()
