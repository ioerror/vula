<!-- README.md for vula documentation -->

This file describes how to submit changes to the vula web documentation. The 
documentation website is powered by a static site generator, with source and
target directories in different git repositories. With two repositories, we 
avoid cluttering the vula git history with generated files.

# Software requirements

[git](https://git-scm.com/)
[hugo](https://gohugo.io/)

About Hugo: We use hugo locally to render HTML files that are pushed to the 
[*vula-pages*](https://codeberg.org/vula/pages) repo, where they populate the 
[vula.link](https://vula.link) website. 

## First-time setup

1. On [codeberg.org](codeberg.org), fork the 
[*vula*](https://codeberg.org/vula/vula) and 
[*pages*](https://codeberg.org/vula/pages) repositories.

2. Clone your forked *vula* and *pages* repositories locally as follows:

```
     git clone git@codeberg.org:<your_account>/vula.git vula
     git clone git@codeberg.org:<your_account>/pages.git vula-pages    
```

## Making changes to the document source files (in the vula repo)

1. Make sure that your local vula repository is up-to-date:

```
     git checkout main
     git pull
```

2. Create and check out a working git branch.

```
     git checkout -b <working_branch_name>
```

3.  Using a text editor, add, modify, or delete documentation files in the 
following location:

```
     vula/www-vula/
```

4. Save your changes.

5. Run one of the `make` options.

     a. *make build* -- This command runs hugo to render the source files into 
     HTML and to deposit the resulting files in the vula-pages file tree.

     b. *make preview* -- Same as `make build`, but also starts a local hugo 
     server where you can view the HTML files and make further changes 
     interactively. Use a web browser to access the server at 
     http://localhost:1313. Changes that you make in this mode are re-rendered 
     and saved automatically.

6. When finished, commit and push your changes.

```
     git commit -a -m “<message>"
     git push
```

Or, interactively,

```
     git add -p
     git commit -m “<message>"
     git push
```

7. Open a PR on the website using the link displayed after you pushed.

## Managing the HTML output files (in the vula-pages repo)

1. Make sure that your local vula-pages repository is up-to-date:

```
     git checkout main
     git pull
     git status
```

Output from `git status` should show that you are on main and that the re-
rendered files have been changed.

2. Create and check out a working git branch.

```
     git checkout -b <working_branch_name>
```

3. Commit and push your changes.

```
     git commit -a -m “<message>"
     git push
```

Or, interactively,

```
     git add -p
     git commit -m “<message>"
     git push
```

4. Open a PR on the website using the link displayed after you pushed.
