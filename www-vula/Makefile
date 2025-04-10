help:
	@echo
	@echo "Before using this file, consult README-docs.md in the"
	@echo "vula repository root."
	@echo
	@echo "We use hugo, a static site generator, to render the"
	@echo "documentation files as HTML and write them to" 
	@echo "vula-pages, the webserver repo. We offer two hugo"
	@echo "build modes that are called with the following targets:"
	@echo 
	@echo " build    - Builds and writes the HTML."
	@echo " preview  - Same as 'build', but also starts the hugo"
	@echo "            local server, which lets you preview the"
	@echo "            website. While the server is running, any" 
	@echo "            changes to the source files are rendered"
	@echo "            and saved in real time. Instructions for" 
	@echo "            using the server are provided in stdout."
	@echo

build:
	hugo 

preview:
	hugo server --disableFastRender

