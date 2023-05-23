PKGNAME=$(shell grep -s '^__name__\s*=' setup.py | sed -e 's/^__name__\s*=\s*//')
PKGVERSION=$(shell grep -s '^__version__\s*=' setup.py | sed -e 's/^__version__\s*=\s*//')
RELEASE=$(shell grep Release: *.spec | cut -d"%" -f1 | sed 's/^[^:]*:[^0-9]*//')
DIST=$(shell rpm --eval '%dist')
BUILD=$(shell pwd)/build

default:
	@echo "Nothing to do"

dist:
	@echo "-- python build dist --"
	@python3 setup.py sdist
	@mv dist/${PKGNAME}-${PKGVERSION}.tar.gz .
	@rm -r dist

sources: dist
	@mkdir -p $(BUILD)
	@cp ${PKGNAME}-${PKGVERSION}.tar.gz $(BUILD)/

prepare: sources
	@mkdir -p $(BUILD)/RPMS/noarch
	@mkdir -p $(BUILD)/SRPMS/
	@mkdir -p $(BUILD)/SPECS/
	@mkdir -p $(BUILD)/SOURCES/
	@mkdir -p $(BUILD)/BUILD/
	cp $(BUILD)/${PKGNAME}-${PKGVERSION}.tar.gz $(BUILD)/SOURCES
	cp ${PKGNAME}.spec $(BUILD)/SPECS

srpm: prepare
	@echo "-- Building srpm --"
	@rpmbuild -bs --define="dist $(DIST)" --define="_topdir $(BUILD)" $(BUILD)/SPECS/$(PKGNAME).spec

rpm: srpm
	@echo "-- Building rpm --"
	@rpmbuild --rebuild --define="dist $(DIST)" --define="_topdir $(BUILD)" $(BUILD)/SRPMS/$(PKGNAME)-$(PKGVERSION)-$(RELEASE)$(DIST).src.rpm

clean:
	@echo "-- Cleaning --"
	@rm -rf build dist
	@rm -rf ${PKGNAME}-${PKGVERSION}.tar.gz
	@find . -name '${PKGNAME}.egg-info' -exec rm -fr {} +
	@find . -name '${PKGNAME}.egg' -exec rm -f {} +

.PHONY: dist srpm rpm sources clean