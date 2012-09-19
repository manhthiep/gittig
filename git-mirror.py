#!/usr/bin/env python

# Original idea & copyright: https://launchpad.net/linaro-android-gerrit-support
# git-mirror.py - v1.0

import os
import sys
import time
import optparse
import logging
import urlparse
from xml.dom import minidom

# Magic name for mirror dstination remote
CONFIG_KEYWORD = "CONFIG"
CONFIG_FILE = "mirror.conf"

conf = None
options = None

# git-mirror.py clone --manifest=<manifest-file> [..]
# git-mirror.py clone --url=<project-url> [..]
# git-mirror.py fetch [..]
# git-mirror.py sync --manifest=<manifest-file> [..]
# Other optional arguments:
#   --mirror-dir=<mirror-dir>
#   --config=<config-file>
#   --upstream=<upstream-url>
#   --dry-run
#   --debug
optparser = optparse.OptionParser(usage="""%prog <options> <command> <args>...

Command:
  clone  - Clone any new projects from source upstreams (based on config)
  fetch  - Fetch upstream updates (based on working copy)
  sync   - Sync projects (based on working copy or manifest)""")

optparser.add_option("-d", "--mirror-dir", metavar="DIR",
             dest="mirror_dir",
             help="Mirror root directory")
optparser.add_option("-c","--config", default="mirror.conf",
             dest="config",
             help="Config file to use (%default)")
optparser.add_option("-m","--manifest", metavar="NAME.xml",
             dest="manifest",
             help="Use manifest for list of upstream projects")
optparser.add_option("-u","--url", metavar="URL",
             dest="url",
             help="URL to git project")
optparser.add_option("--upstream", metavar="SUBSTR", default="",
             help="Process only upstreams matching SUBSTR")
optparser.add_option("--dry-run", action="store_true",
             help="Don't make any changes")
optparser.add_option("-D","--debug", action="store_true",
             dest="debug",
             help="Enable debug logging")

log = logging.getLogger(__file__)

class MirrorConfig(object):

    def __init__(self, mirror_dir):
        self.remotes = {}
        self.configs = {}
        self.basedir = mirror_dir

    def store_remote_rules(self, remote, remote_vars, remote_rules):
        if remote and self.get_bool(remote_vars.get("active", "true")):
            self.remotes[remote] = (remote_vars, remote_rules)

    def get_bool(self, val):
        val2 = val.lower()
        if val2 in ("true", "on", "1"):
            return True
        if val2 in ("false", "off", "0"):
            return False
        assert False, "Syntax error: boolean value expected, got: " + val

    def parse(self, config_file):
        in_file = open(config_file)
        remote = None
        remote_vars = {}
        remote_rules = {}
        config_section = 0
        for line in in_file:
            line = line.strip()
            if not line:
                continue
            if line[0] == "#":
                # Comment line, ignore
                continue
            if line[0] == "[":
                # Start of new section
                if not remote == None:
                    # Store previous parsed remote vars & rules
                    self.store_remote_rules(remote, remote_vars, remote_rules)
                remote = line[1:-1]
                if not remote.startswith(CONFIG_KEYWORD):
                    # Start of remote config
                    config_section = 0              
                    assert "://" in remote, "URL schema is required in " + line
                    remote_rules = {}
                    remote_vars = {}
                else:
                    # Start of git-mirror tool config
                    config_section = 1
            else:
                fields = line.split("=", 1)
                fields = [f.strip() for f in fields]
                if fields[0][0] == "$":
                    # Variable spec
                    if config_section == 1:
                        self.configs[fields[0][1:]] = fields[1]
                    else:
                        remote_vars[fields[0][1:]] = fields[1]
                else:
                    # Repository rule spec (only in remote config section)
                    if config_section == 0:
                        if len(fields) == 1:
                            fields.append(fields[0])
                        remote_rules[fields[0]] = fields[1]
        # Store last remote config section
        if config_section == 0:
            self.store_remote_rules(remote, remote_vars, remote_rules)
        in_file.close()

    def store(self, config_file):
        in_file = open(config_file)
        in_file.close()

    def disable_remote_configs(self):
        self.remotes.clear()

    def get_mirror_dir(self):
        return self.basedir.rstrip("/")

    def add_remote(self, remote):
        if self.remotes.has_key(remote):
            log.debug("Remote '%s' already defined. Skip.", remote)
        else:
            remote_var = {}
            remote_rules = {}
            self.remotes[remote] = (remote_var, remote_rules)

    def get_remotes(self, substr_match=""):
        return sorted([r for r in self.remotes.keys() if substr_match in r and not r.startswith(CONFIG_KEYWORD)])

    def get_var(self, remote, var):
        return self.remotes[remote][0].get(var)

    def has_remote(self, remote):
        return remote in self.remotes

    def add_project_to_remote(self, remote, src_project, dst_path):
        if self.remotes[remote][1].has_key(src_project):
            log.debug("Project '%s' already in remote '%s'. Skip", src_project, remote)
        else:
            self.remotes[remote][1].setdefault(src_project, dst_path)

    def get_mirror_project(self, remote, src_project):
        """Get mirror path for a project. By default it is equal
        to source path, but if exception was defined, it is different."""
        return self.remotes[remote][1].get(src_project, src_project)

    def get_project_map(self, remote):
        """Get all mirror project paths as dict (key - src path, value - dst path)"""
        return self.remotes[remote][1]

def run_command(cmdline, favor_dry_run=True):
    err = 0
    if favor_dry_run and options.dry_run:
        log.info("Would run: %s", cmdline)
    else:
        log.debug("Running: %s", cmdline)
        err = os.system(cmdline)
    return err    

def scan_git_projects(basedir):
    git_projects = []
    for root, dirs, files in os.walk(basedir):
        for d in dirs:
            if d.endswith(".git"):
                abspath = os.path.join(root, d)
                relpath = abspath[len(basedir):]
                git_projects.append((os.path.abspath(abspath), relpath))
    return git_projects

def get_manifest_projects(manifest):
    log.info("Parsing manifest file '%s'", os.path.abspath(manifest))
    dom = minidom.parse(manifest)
    remote_alias = {}
    # Get remote list
    for r in dom.getElementsByTagName("remote"):
        remote_s = r.getAttribute("fetch").rstrip("/")
        conf.add_remote(remote_s)
        remote_alias[r.getAttribute("name")] = (remote_s)
    # Get default remote
    default_remote = ""
    default_list = dom.getElementsByTagName("default")
    if len(default_list) >= 1:
        if len(default_list) > 1:
            log.info("Multiple default remote in manifest. Take only fist item")
        default_remote = default_list[0].getAttribute("remote")
    # Get all projects
    for p in dom.getElementsByTagName("project"):
        project_src = p.getAttribute("name")
        project_dst_path = p.getAttribute("path")
        project_remote_alias = p.getAttribute("remote")
        if project_remote_alias == "":
            if default_remote == "":
                log.info("This project does not specify remote :(")
            else:
                project_remote_alias = default_remote
        if remote_alias.has_key(project_remote_alias):
            remote_s = remote_alias.get(project_remote_alias)       
            log.debug("Add project '%s' for remote '%s'.", project_src, project_remote_alias)
            if project_dst_path == "":     
                conf.add_project_to_remote(remote_s, project_src, project_src)
            else:
                conf.add_project_to_remote(remote_s, project_src, project_dst_path)
        else:
            log.info("Skip project '%s' for remote '%s'.", project_src, project_remote_alias)        

def get_project_map_for_a_remote(remote):
    """Get {src: dst} project map for a remote"""
    projects = conf.get_project_map(remote)
    projects_d = {}
    log.debug("Remote %s:", remote)
    for p in projects:
        dst_path = projects.get(p, p)
        if dst_path == "skip":
            log.debug("Skip downloading '%s' (forced by config)", p)
        else:
            log.debug("Download '%s' --> '%s'", p, dst_path)
            projects_d[p] = dst_path
    return projects_d

def clone_projects(remote, basedir, git_projects):
    """Clone-mirror projects from remote server"""
    err = 0
    count = 0
    total = len(git_projects)
    for p in git_projects:
        count = count + 1
        if os.path.exists(basedir.rstrip("/") + "/" + p + ".git"):
            log.info("'%s' already exists, skipping (%d/%d)", p, count, total)
            continue
        dir = os.path.dirname(p)
        dir = os.path.join(basedir, dir)
        try:
            os.makedirs(dir)
        except OSError:
            pass
        log.info("Enter %s", dir)
        log.info("Cloning %s/%s.git (%d/%d)", remote, p, count, total)
        os.chdir(dir)
        cmd = "git clone --mirror %s/%s.git" % (remote, p)
        err = run_command(cmd)
        if not err == 0:
            log.info("Error occurs (%d). Abort", err)
            return err
        #os.chdir(basedir)
    return 0

def fetch_projects(git_projects):
    """Update locally present mirror projects from remote server"""
    err = 0
    count = 0
    total = len(git_projects)
    for abspath, relpath in git_projects:
        count = count + 1
        log.info("Fetching " + relpath + " (%d/%d)", count, total)
        os.chdir(abspath)
        err = run_command("git fetch")
        if not err == 0:
            log.info("Error occurs (%d). Abort", err)
            return err
    return 0

def sync_projects(remote, basedir, git_projects):
    """Update present mirror projects from remote server. Clone if not exist"""
    err = 0
    count = 0
    total = len(git_projects)
    for p in git_projects:
        count = count + 1
        p_path = basedir.rstrip("/") + "/" + p + ".git"
        if os.path.exists(p_path):
            # Fetch existing mirror
            log.debug("'%s' already exists, fetching...", p)
            log.info("Syncing %s/%s.git... (%d/%d)", remote, p, count, total)
            os.chdir(p_path)
            err = run_command("git fetch")
            if not err == 0:
                log.info("Error occurs (%d). Abort", err)
                return err
            continue
        else:
            # Clone non-existent mirror
            dir = os.path.dirname(p)
            dir = os.path.join(basedir, dir)
            try:
                os.makedirs(dir)
            except OSError:
                pass
            log.debug("'%s' doesnt' exist, cloning...", p)
            log.info("Syncing %s/%s.git...", remote, p)
            os.chdir(dir)
            cmd = "git clone --mirror %s/%s.git" % (remote, p)
            err = run_command(cmd)
            if not err == 0:
                log.info("Error occurs (%d). Abort", err)
                return err
        #os.chdir(basedir)
    return 0

def check_args(optparser, args, expected):
    if len(args) != expected:
        optparser.error("Wrong number of arguments")

def do_sub_command(sub_command):
    if sub_command == "clone":
        if options.manifest:
            get_manifest_projects(options.manifest)
            for remote in conf.get_remotes(options.upstream.rstrip("/")):
                git_projects = get_project_map_for_a_remote(remote).keys()
                git_projects.sort()
                remote_p = urlparse.urlparse(remote)
                log.info("=== Processing: %s (%d Repositories) ===", remote, len(git_projects))
                remote_basedir = conf.get_mirror_dir() + "/" + remote_p.netloc.rstrip("/") + remote_p.path
                clone_projects(remote, remote_basedir, git_projects)
        elif options.url:
            git_projects = []
            s = options.url.rfind("/")
            remote = options.url[:s]
            git_projects.append(options.url[s+1:-len(".git")])
            remote_p = urlparse.urlparse(remote)
            log.info("=== Processing: %s (%d Repositories) ===", remote, len(git_projects))
            remote_basedir = conf.get_mirror_dir() + "/" + remote_p.netloc.rstrip("/") + remote_p.path
            clone_projects(remote, remote_basedir, git_projects)
        else:
            optparser.error("Please provide git project(s) by --manifest or --url")

    elif sub_command == "fetch":
        for remote in conf.get_remotes(options.upstream.rstrip("/")):
            remote_p = urlparse.urlparse(remote)
            log.info("Scanning mirrors...")
            remote_basedir = conf.get_mirror_dir() + "/" + remote_p.netloc.rstrip("/") + remote_p.path
            git_projects = scan_git_projects(remote_basedir)
            git_projects.sort()
            log.info("=== Processing: %s (%d Repositories) ===", remote, len(git_projects))
            fetch_projects(git_projects)

    elif sub_command == "sync":
        if options.manifest:
            get_manifest_projects(options.manifest)
            for remote in conf.get_remotes(options.upstream.rstrip("/")):
                git_projects = get_project_map_for_a_remote(remote).keys()
                git_projects.sort()
                remote_p = urlparse.urlparse(remote)
                remote_basedir = conf.get_mirror_dir() + "/" + remote_p.netloc.rstrip("/") + remote_p.path
                log.info("=== Processing: %s (%d Repositories) ===", remote, len(git_projects))
                sync_projects(remote, remote_basedir, git_projects)
        else:
            optparser.error("Please provide git project(s) by --manifest or --url")

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
    if options.mirror_dir:
        # Provided path
        mirror_dir = os.path.abspath(options.mirror_dir)
    else:
        # Current directory
        mirror_dir = os.getcwd()

    if not os.path.isdir(mirror_dir):
        optparser.error("Mirror dir is not exist in provided path (--mirror-dir)")

    conf = MirrorConfig(mirror_dir)
    # Read configs from file
    if options.config:
        if os.path.isfile(options.config):
            # Config file in provided path
            log.info("Reading config file '%s'", options.config)
            conf.parse(options.config)
        else:
            optparser.error("Config file is not exist in provided path (--config)")
    elif os.path.isfile(conf.get_mirror_dir() + "/" + CONFIG_FILE):
        # Config file under mirror dir
        log.info("Reading config file '%s'", conf.get_mirror_dir() + "/" + CONFIG_FILE)
        conf.parse(conf.get_mirror_dir() + "/" + CONFIG_FILE)
    elif os.path.isfile(os.path.abspath(CONFIG_FILE)):
        # Config file under current directory
        log.info("Reading config file '%s'", os.path.abspath(CONFIG_FILE))
        conf.parse(os.path.abspath(CONFIG_FILE))

    do_sub_command(args[0])

if __name__ == "__main__":
    main()

