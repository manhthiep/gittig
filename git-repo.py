#!/usr/bin/env python

# Original idea & copyright: https://launchpad.net/linaro-android-gerrit-support
# git-repo.py - v1.0

import os
import sys
import time
import optparse
import logging
import urlparse
from xml.dom import minidom

# Magic name for mirror dstination remote
CONFIG_KEYWORD = "CONFIG"
CONFIG_FILE = "repo.conf"

conf = None
options = None

# Example commands:
# git-repo.py clone --manifest=<manifest-file> [..]
# git-repo.py sync [..]
# git-repo.py sync --project=<project-local-path>[..]
# git-repo.py sync --manifest=<manifest-file> --project=<project-local-path/project-name>[..]
# Other optional arguments:
#   --local-dir=<local-dir>
#   --config=<config-file>
#   --remote=<remote-url>
#   --dry-run
#   --debug
optparser = optparse.OptionParser(usage="""%prog <options> <command> <args>...

Command:
  clone  - Clone any new projects from source (based on config & manifest)
  sync   - Sync remote updates (based on working copy or manifest)""")

optparser.add_option("-d", "--local-dir", metavar="DIR",
             dest="local_dir",
             help="Local root directory")
optparser.add_option("-c","--config", default="repo.conf",
             dest="config",
             help="Config file to use (%default)")
optparser.add_option("-m","--manifest", metavar="NAME.xml",
             dest="manifest",
             help="Use manifest for list of projects")
optparser.add_option("-p", "--project", metavar="DIR", default="",
             dest="project", 
             help="Project name or project local path to clone/sync")
optparser.add_option("-r","--remote", metavar="SUBSTR", default="",
             dest="remote",
             help="Process only remote matching SUBSTR (use with clone)")
optparser.add_option("--dry-run", action="store_true",
             help="Don't make any changes")
optparser.add_option("-D","--debug", action="store_true",
             dest="debug",
             help="Enable debug logging")

log = logging.getLogger(__file__)

class GitProject(object):

    def __init__(self, name, path, remote, revision):
        self.name = name
        self.path = path
        self.remote_url = remote + "/" + name + ".git"
	self.revision = revision

    def clone(self, basedir):
        dir = os.path.join(basedir, self.path)
        if os.path.exists(dir):
            log.info("'%s' already exists, skipping", self.path)
            return 0
        os.chdir(basedir)
        log.debug("Enter %s", basedir)
        log.info("Cloning %s", self.remote_url)
        if self.revision == "":     
            cmd = "git clone %s %s" % (self.remote_url, self.path)
        else:
            cmd = "git clone %s -b %s %s" % (self.remote_url, self.revision, self.path)
        err = run_command(cmd)
        if not err == 0:
            log.info("Error occurs (%d). Abort", err)
            os.chdir(basedir)
            return err
        return 0
    
class GitRemote(object):
    
    def __init__(self, name, fetch):
        self.name = name
        self.fetch_url = fetch
        self.projects = []
        self.vars = {}
        self.rules = {}

    def add_project(self, project):
        for p in self.projects:
            if project.name == p.name:
                log.debug("Project '%s' already in remote '%s'. Skip", project.name, self.name)
                return 0
        self.projects.append(project)
        return 1

    def get_projects(self):
        return self.projects

    def store_var(self, var, val):
        self.vars[var] = val

    def get_var(self, var):
        return self.vars.get(var)

    def get_bool(self, val):
        val2 = val.lower()
        if val2 in ("true", "on", "1"):
            return True
        if val2 in ("false", "off", "0"):
            return False
        assert False, "Syntax error: boolean value expected, got: " + val

    def store_rule(self, field1, field2):
        if self.get_bool(self.vars.get("active", "true")):
            self.rules[field1] = field2

    def get_rules(self):
        return self.rules

class RepoConfig(object):

    def __init__(self, local_dir):
        self.configs = {}
        self.remotes = []
        self.local_dir = local_dir

    def parse(self, config_file):
        in_file = open(config_file)
        git_remote = None
        config_section = 0
        for line in in_file:
            line = line.strip()
            if not line:
                continue
            if line[0] == "#":
                continue
            if line[0] == "[":
                # Declare new remote
                remote_url = line[1:-1]
                if not remote_url.startswith(CONFIG_KEYWORD):
                    assert "://" in remote_url, "URL schema is required in " + line
                    git_remote = GitRemote("from_config", remote_url)       
                    self.remotes.append(git_remote)
                    config_section = 0
                else:
                    config_section = 1
            else:
                fields = line.split("=", 1)
                fields = [f.strip() for f in fields]
                if fields[0][0] == "$":
                    # Variable spec
                    # $<var-name> = <value>
                    if config_section == 0:
                        if not git_remote == None:
                            git_remote.store_var(fields[0][1:], fields[1])
                        else:
                            assert False, "Syntax error: Variable is defined not within remote."
                    else:
                        self.configs[fields[0][1:]] = fields[1]
                else:
                    # Repository rule spec
                    # <project-name> = <dest-path> or 'skip'
                    if not config_section == 0:
                        assert False, "Syntax error: Rules are defined only within remote."
                    else:
                        if len(fields) == 1:
                            fields.append(fields[0])
                        if not git_remote == None:
                            git_remote.store_rule(fields[0], fields[1])
                        else:
                            assert False, "Syntax error: Rule is defined not within remote."
        # Done, close file
        in_file.close()

    def store(self, config_file):
        in_file = open(config_file)
        in_file.close()

    def get_local_dir(self):
        return self.local_dir.rstrip("/")

    def add_remote(self, remote):
        for r in self.remotes:
            if r.fetch_url == remote.fetch_url or r.name == remote.name:
                log.debug("Remote '%s' already defined. Skip.", remote.fetch_url)
                if r.name == "from_config":
                    r.name = remote.name
                return 0
        self.remotes.append(remote)
        return 1

    def find_remote(self, name):
        for r in self.remotes:
            if r.name == name:
                return r
        return None

    def get_remotes(self, substr_match=""):
        remotes = []
        for r in self.remotes:
            if substr_match in r.fetch_url:
                remotes.append(r)
        return sorted(remotes, key=lambda remote: remote.fetch_url)

    def add_project_to_remote(self, git_remote, git_project):
        return git_remote.add_project(git_project)

def run_command(cmdline, favor_dry_run=True):
    err = 0
    if favor_dry_run and options.dry_run:
        log.info("Would run: %s", cmdline)
    else:
        log.debug("Running: %s", cmdline)
        err = os.system(cmdline)
    return err

def scan_projects(basedir):
    projects = []
    for root, dirs, files in os.walk(basedir):
        for d in dirs:
            if d.endswith(".git"):
                abspath = os.path.join(root, d[:-len(".git")])
                relpath = abspath[len(basedir):]
                log.debug("abspath=%s, relpath=%s", abspath, relpath)
                projects.append((os.path.abspath(abspath), relpath))
    projects.sort()
    return projects

def get_manifest_projects(manifest):
    log.info("Parsing manifest file '%s'", os.path.abspath(manifest))
    dom = minidom.parse(manifest)
    # Get remote list
    for r in dom.getElementsByTagName("remote"):
        r_name = r.getAttribute("name")
        r_fetch_url = r.getAttribute("fetch").rstrip("/")
        git_remote = GitRemote(r_name, r_fetch_url)
        conf.add_remote(git_remote)
    # Get default remote
    default_remote_alias = ""
    default_conf = dom.getElementsByTagName("default")
    if len(default_conf) >= 1:
        if len(default_conf) > 1:
            log.info("Multiple default remote in manifest. Take only fist item")
        default_remote_alias = default_conf[0].getAttribute("remote")
    # Get all projects
    for p in dom.getElementsByTagName("project"):
        p_name = p.getAttribute("name")
        p_path = p.getAttribute("path")
        p_remote_alias = p.getAttribute("remote")
        p_revision = p.getAttribute("revision")        
        # Assign to default remote if the project does not specify
        if p_remote_alias == "":
            if default_remote_alias == "":
                log.info("This project is not belong any remote :(")
            else:
                p_remote_alias = default_remote_alias
        # Find the remote object
        git_remote = conf.find_remote(p_remote_alias)
        if not git_remote == None:
            log.debug("Add project '%s' for remote '%s'.", p_name, p_remote_alias)
            if p_path == "":     
                git_project = GitProject(p_name, p_name, git_remote.fetch_url, p_revision)
            else:
                git_project = GitProject(p_name, p_path, git_remote.fetch_url, p_revision)
            conf.add_project_to_remote(git_remote, git_project)
        else:
            log.info("Skip project '%s' for remote '%s'.", p_name, p_remote_alias)        

def get_projects_for_a_remote(remote, p_match_str=""):
    """Get projects for a remote (rules applied)"""
    projects = remote.get_projects()
    rules = remote.get_rules()
    projects_d = []
    log.debug("Remote %s:", remote.fetch_url)
    for p in projects:
        if rules.has_key(p.name):
            val = rules.get(p.name)
            if  val == "skip":
                log.debug("Skip downloading '%s' (forced by config)", p.name)
            else:
                log.debug("Download '%s' --> '%s'", p.name, val)
                p.path = val
                projects_d.append(p)
        else:
            log.debug("Download '%s' --> '%s'", p.name, p.path)
            projects_d.append(p)
    if not p_match_str == "":
        projects_f = []
        for p in projects_d:
            if p_match_str in p.path or p_match_str in p.name:
                projects_f.append(p)
        return projects_f      
    return sorted(projects_d, key=lambda project: project.path)

def get_project(p_match_str):
    """Get projects which have path or name matches with p_match_str"""
    projects_f = []
    if p_match_str == "":
        log.info("None project matches.")
    else:
        # Scan all remotes
        for remote in conf.get_remotes(""):
            projects = get_projects_for_a_remote(remote, p_match_str)
            for p in projects:
                projects_f.append(p)
    return projects_f

def clone_projects(remote, basedir, projects):
    """Clone projects from remote server"""
    count = 0
    total = len(projects)
    if total == 0:
        log.info("Nothing to clone.")
    else:
        os.chdir(basedir)
        log.info("Enter %s", basedir)
        for p in projects:
            count = count + 1
            log.info("Cloning projects: (%d/%d)", count, total)
            if not p.clone(basedir) == 0:
                return

def sync_projects(projects):
    """Update projects from remote server"""
    count = 0
    err = 0
    total = len(projects)
    if total == 0:
        log.info("Nothing to sync.")
    for abspath, relpath in projects:
        count = count + 1
        if not os.path.isdir(abspath):
            log.info("'%s' does not exists. Remember clone it before syncing.", relpath)
        else:
            log.info("Syncing " + relpath + " (%d/%d)", count, total)
            os.chdir(abspath)
            err = run_command("git pull")
            if not err == 0:
                return

def check_args(optparser, args, expected):
    if len(args) != expected:
        optparser.error("Wrong number of arguments")

def do_sub_command(sub_command):
    if sub_command == "clone":
        if options.manifest:
            get_manifest_projects(options.manifest)
            for remote in conf.get_remotes(options.remote):
                projects = get_projects_for_a_remote(remote, options.project)
                log.info("=== Processing: %s (%d Repositories) ===", remote.fetch_url, len(projects))
                clone_projects(remote, conf.get_local_dir() + "/", projects)
        else:
            optparser.error("Please provide git project(s) by --manifest")
    elif sub_command == "sync":
        if options.manifest:
            projects_f1 = []
            projects_f2 = []
            get_manifest_projects(options.manifest)
            projects_f1 = get_project(options.project)
            for p in projects_f1:
                abspath = os.path.join(conf.get_local_dir() + "/", p.path)
                relpath = abspath[len(conf.get_local_dir() + "/"):]
                projects_f2.append((os.path.abspath(abspath), relpath))
            sync_projects(projects_f2)
        else:
            log.info("Scanning repos in '%s'...", conf.get_local_dir())
            projects = scan_projects(conf.get_local_dir() + "/")
            if options.project:           
                projects_f = []
                for abspath, relpath in projects:
                    if relpath.startswith(options.project):
                        projects_f.append((abspath, relpath))
                sync_projects(projects_f)
            else:
                log.info("=== Processing: %d Repositories ===", len(projects))
                sync_projects(projects)
    else:
        optparser.error("Unknown command")

def main():
    global conf
    global options

    options, args = optparser.parse_args(sys.argv[1:])
    if len(args) < 1:
        optparser.error("Wrong number of arguments")

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG if options.debug else logging.INFO)

    # Mirror directory settings
    if options.local_dir:
        # Provided path
        local_dir = os.path.abspath(options.local_dir)
    else:
        # Current directory
        local_dir = os.getcwd()

    if not os.path.isdir(local_dir):
        optparser.error("Mirror dir is not exist in provided path (--local-dir)")

    conf = RepoConfig(local_dir)
    # Read configs from file
    if options.config:
        if os.path.isfile(options.config):
            # Config file in provided path
            log.info("Read config file '%s'", options.config)
            conf.parse(options.config)
        else:
            optparser.error("Config file is not exist in provided path (--config)")
    elif os.path.isfile(conf.get_local_dir() + "/" + CONFIG_FILE):
        # Config file under mirror dir
        log.info("Read config file '%s'", conf.get_local_dir() + "/" + CONFIG_FILE)
        conf.parse(conf.get_local_dir() + "/" + CONFIG_FILE)
    elif os.path.isfile(os.path.abspath(CONFIG_FILE)):
        # Config file under current directory
        log.info("Read config file '%s'", os.path.abspath(CONFIG_FILE))
        conf.parse(os.path.abspath(CONFIG_FILE))

    do_sub_command(args[0])

if __name__ == "__main__":
    main()

