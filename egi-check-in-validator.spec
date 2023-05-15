%define name egi-check-in-validator
%define version 0.2.2
%define release 1
%define logrotate_dir logrotate.d

Summary: A plugin for checking if an Access Token issued by EGI Check-in is valid. This plugin can be used by HTCondor-CE and ARC-CE
Name: %{name}
Version: %{version}
Release: %(echo $GIT_COMMIT_DATE).%(echo $GIT_COMMIT_HASH)%{?dist}
Source0: %{name}-%{version}.tar.gz
License: ASL 2.0
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: nikosev <nikos.ev@hotmail.com>
Url: https://github.com/rciam/check-in-validator-plugin

%description
A plugin for checking if an Access Token issued by EGI Check-in is valid. This plugin can be used by HTCondor-CE and ARC-CE.
More information in %{Url}

%prep
%setup -n %{name}-%{version} -n %{name}-%{version}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install --directory -m 644 %{buildroot}%{_sysconfdir}/%{name}/
install --directory -m 644 %{buildroot}%{_sysconfdir}/%{name}/config
install --directory -m 644 %{buildroot}%{_localstatedir}/log/%{name}
cp config/example-egi-check-in-validator.ini %{buildroot}%{_sysconfdir}/%{name}/config/egi-check-in-validator.ini
cp config/logger.ini %{buildroot}%{_sysconfdir}/%{name}/config/
cp config/logrotate.conf %{buildroot}%{_sysconfdir}/%{logrotate_dir}/%{name}
touch %{buildroot}%{_localstatedir}/log/%{name}/egi-check-in-validator.log

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%{_sysconfdir}/%{name}/config/egi-check-in-validator.ini
%{_sysconfdir}/%{name}/config/logger.ini
%{_localstatedir}/log/%{name}/egi-check-in-validator.log
%{_sysconfdir}/%{logrotate_dir}/%{name}
%defattr(-,root,root)
