
=======
git-tools
=========

Summary
---------------

# Original ideas & Copyright: https://launchpad.net/linaro-android-gerrit-support
# List of tools
  
  [1]. git-mirror.py: for creating/fetching local git mirrors
       Results as following
            <mirror-root-dir>/<remote-url>/<project-path>
       Example:
            <mirror-root-dir>
                  |---- android.git.linaro.org
                  |                  |---------device/...
                  |                  |---------platform/...
                  |---- android.googlesource.com
                  |---- github.com
                              |-------- manhthiep/
                              |-------- CyanogenMod/
                              |-------- Evervolv/
       Commands:
            git-mirror.py clone --manifest=<manifest-file> [..]
            git-mirror.py clone --url=<project-url> [..]
            git-mirror.py fetch [..]
       Other options:
            --mirror-dir=<mirror-dir> 
            --config=<config-file>
            --upstream=<upstream-url>
            --dry-run
            --debug
       Config file: [mirror.conf]
            Syntax:
                 [config-section/remote-name]
                 #comment
                 $var = val
                 <src-path> = <local-path> #mapping rule

   [2]. git-repo.py: for creating/syncing git projects based on manifest file.
        Results similar to Google's repo tool (except .repo directory)
        Commands:
            git-repo.py clone --manifest=<manifest-file> [..]
            git-repo.py sync [..]
            git-repo.py sync --project=<project-local-path>[..]
            git-repo.py sync --manifest=<manifest-file> --project=<project-local-path/project-name>[..]
        Other options:
            --local-dir=<local-dir>
            --config=<config-file>
            --remote=<remote-url>
            --dry-run
            --debug
        Config file: [repo.conf]
            Syntax:
                 [config-section/remote-name]
                 #comment
                 $var = val
                 <src-path> = <local-path> #mapping rule

Change logs
---------------
2012/09/15: Initial commit
            git-mirror.py - v1.0
            git-repo.py - v1.0
            Added example manifests
