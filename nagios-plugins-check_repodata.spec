Name:           nagios-plugins-check_repodata
Version:        0.2
Release:        1%{?dist}
Summary:        A Nagios / Icinga plugin for checking sync states of repositories managed by Spacewalk, Red Hat Satellite or SUSE Manager

Group:          Applications/System
License:        GPL
URL:            https://github.com/stdevel/check_repodata
Source0:        nagios-plugins-check_repodata-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

#BuildRequires:
Requires:       rhnlib

%description
This package contains a Nagios / Icinga plugin for checking sync states of repositories managed by Spacewalk, Red Hat Satellite or SUSE Manager

Check out the GitHub page for further information: https://github.com/stdevel/check_repodata

%prep
%setup -q

%build
#change /usr/lib64 to /usr/lib if we're on i686
%ifarch i686
sed -i -e "s/usr\/lib64/usr\/lib/" check_repodata.cfg
%endif

%install
install -m 0755 -d %{buildroot}%{_libdir}/nagios/plugins/
install -m 0755 check_repodata.py %{buildroot}%{_libdir}/nagios/plugins/check_repodata
%if 0%{?el7}
        install -m 0755 -d %{buildroot}%{_sysconfdir}/nrpe.d/
        install -m 0755 check_repodata.cfg  %{buildroot}%{_sysconfdir}/nrpe.d/check_repodata.cfg
%else
        install -m 0755 -d %{buildroot}%{_sysconfdir}/nagios/plugins.d/
        install -m 0755 check_repodata.cfg  %{buildroot}%{_sysconfdir}/nagios/plugins.d/check_repodata.cfg
%endif



%clean
rm -rf $RPM_BUILD_ROOT

%files
%if 0%{?el7}
        %config %{_sysconfdir}/nrpe.d/check_repodata.cfg
%else
        %config %{_sysconfdir}/nagios/plugins.d/check_repodata.cfg
%endif
%{_libdir}/nagios/plugins/check_repodata


%changelog
* Fri Mar 06 2015 Christian Stankowic <info@stankowic-development.net> - 0.2.1
- Fixed RPM version to match script version
- added -o / --logical-and, -p / --positive-filter and -n / --negative-filter parameters (thanks for your contribution, photoninger!)

* Fri Mar 06 2015 Christian Stankowic <info@stankowic-development.net> - 1.0.1
- First release
