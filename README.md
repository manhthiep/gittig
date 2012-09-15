git-tools
=========

Summary
---------------

Original ideas & Copyright: https://launchpad.net/linaro-android-gerrit-support

##List of tools
  
**1. git-mirror.py:** 
For creating/fetching local git mirrors
    * Results as following
    <pre>
    [mirror-root-dir]/[remote-url]/[project-path]
    </pre>
    * Example:
    <pre>
    [mirror-root-dir]
         |---- android.git.linaro.org
         |                  |---------device/...
         |                  |---------platform/...
         |---- android.googlesource.com
         |---- github.com
                   |-------- manhthiep/
                   |-------- CyanogenMod/
                   |-------- Evervolv/
    </pre>
    * Commands:
    <pre>
    git-mirror.py clone --manifest=\<manifest-file\> [..]
    git-mirror.py clone --url=\<project-url\> [..]
    git-mirror.py fetch [..]
    </pre>
    * Other options:
    <pre>
    --mirror-dir=\<mirror-dir\>
    --config=\<config-file\>
    --upstream=\<upstream-url\>
    --dry-run
    --debug
    </pre>
    * Config file: [**mirror.conf**]
         * Syntax:
         <pre>
         [config-section/remote-name]
         #comment
         $var = val
         \<src-path\> = \<local-path\> #mapping rule
         </pre>

**2. git-repo.py:**
For creating/syncing git projects based on manifest file.
    * Results similar to Google's repo tool (except .repo directory)
    * Commands:
    <pre>
    git-repo.py clone --manifest=\<manifest-file\> [..]
    git-repo.py sync [..]
    git-repo.py sync --project=\<project-local-path\>[..]
    git-repo.py sync --manifest=\<manifest-file\> --project=\<project-local-path\/project-name\>[..]
    </pre>
    * Other options:
    <pre>
    --local-dir=\<local-dir\>
    --config=\<config-file\>
    --remote=\<remote-url\>
    --dry-run
    --debug
    </pre>
    * Config file: [**repo.conf**]
        * Syntax:
        <pre>
        [config-section/remote-name]
        #comment
        $var = val
        \<src-path\> = \<local-path\> #mapping rule
        </pre>

Change logs
---------------
* 2012/09/15: 
    * Initial commit
    * git-mirror.py - v1.0
    * git-repo.py - v1.0
    * Added example manifests
