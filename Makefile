PKGNAME=$(shell grep -s '^__name__\s*=' setup.py | sed -e 's/^__name__\s*=\s*//')
PKGVERSION=$(shell grep -s '^__version__\s*=' setup.py | sed -e 's/^__version__\s*=\s*//')
DIST=$(shell rpm --eval '%dist')

default:
	@echo "Nothing to do"

dist:
	@echo "-- python build dist --"
	@python3 setup.py sdist
	@mv dist/${PKGNAME}-${PKGVERSION}.tar.gz .
	@rm -r dist

sources: dist

srpm: dist
	@echo "-- Building srpm --"
	@rpmbuild -ts --define="dist $(DIST)" ${PKGNAME}-${PKGVERSION}.tar.gz

rpm: dist
	@echo "-- Building rpm --"
	@rpmbuild -ta --define="dist $(DIST)" ${PKGNAME}-${PKGVERSION}.tar.gz

clean:
	@echo "-- Cleaning --"
	@rm -rf dist
	@rm -rf ${PKGNAME}-${PKGVERSION}.tar.gz
	@find . -name '${PKGNAME}.egg-info' -exec rm -fr {} +
	@find . -name '${PKGNAME}.egg' -exec rm -f {} +

.PHONY: clean