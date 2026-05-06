.PHONY: apidoc html clean

SPHINXBUILD := sphinx-build
SOURCEDIR := src
BUILDDIR := build
APIDOCDIR := $(SOURCEDIR)/_api
SOURCEPKG := ../src

apidoc:
	$(call log,Generating API documentation)
	@sphinx-apidoc -f -e -o $(APIDOCDIR) $(SOURCEPKG)
	@for f in $(APIDOCDIR)/*.rst; do \
		sed '1s/^src\.//' "$$f" > "$$f.tmp" && mv "$$f.tmp" "$$f"; \
	done
	@rm -f $(APIDOCDIR)/modules.rst $(APIDOCDIR)/src.rst

html: apidoc
	$(call log,Building HTML documentation)
	@$(SPHINXBUILD) -W -b html $(SOURCEDIR) $(BUILDDIR)/html

clean:
	$(call log,Cleaning build artifacts)
	@rm -rf $(BUILDDIR)
