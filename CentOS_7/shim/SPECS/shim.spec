Name:           shim
Version:        12
Release:        2%{?dist}
Summary:        First-stage UEFI bootloader

License:        BSD
URL:            http://www.codon.org.uk/~mjg59/shim/
Source0:	https://github.com/mjg59/shim/releases/download/%{version}/shim-%{version}.tar.bz2
#Source1:	centos.crt
# currently here's what's in our dbx: # nothing.
#Source2:	dbx-x64.esl
#Source3:	dbx-aa64.esl
Source4:	shim-find-debuginfo.sh
Source5:	centos.esl

Patch0:		0001-Add-vendor-esl.patch

BuildRequires: git openssl-devel openssl
BuildRequires: pesign >= 0.106-1
BuildRequires: gnu-efi >= 1:3.0.5-6.el7, gnu-efi-devel >= 1:3.0.5-6.el7

# for xxd
BuildRequires: vim-common

# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
Provides: bundled(openssl) = 1.0.2j

# Shim is only required on platforms implementing the UEFI secure boot
# protocol. The only one of those we currently wish to support is 64-bit x86.
# Adding further platforms will require adding appropriate relocation code.
ExclusiveArch: x86_64 aarch64

%ifarch x86_64
%global efiarch x64
%endif
%ifarch aarch64
%global efiarch aa64
%endif

# Figure out the right file path to use
%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/redhat/'))

%define debug_package %{nil}
%global __debug_package 1

%global _binaries_in_noarch_packages_terminate_build 0

%description
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments.

%package -n shim-unsigned-%{efiarch}
Summary: First-stage UEFI bootloader (unsigned data)

%description -n shim-unsigned-%{efiarch}
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments.

%package -n shim-unsigned-%{efiarch}-debuginfo
Obsoletes: shim-debuginfo < 0.9
Summary: Debug information for package %{name}
Group: Development/Debug
AutoReqProv: 0
BuildArch: noarch

%description -n shim-unsigned-%{efiarch}-debuginfo
This package provides debug information for package %{name}.
Debug information is useful when developing applications that use this
package or when debugging this package.

%ifarch x86_64
%package -n shim-unsigned-ia32
Summary: First-stage UEFI bootloader (unsigned data)

%description -n shim-unsigned-ia32
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments.

%package -n shim-unsigned-ia32-debuginfo
Obsoletes: shim-debuginfo < 0.9
Summary: Debug information for package %{name}
Group: Development/Debug
AutoReqProv: 0
BuildArch: noarch

%description -n shim-unsigned-ia32-debuginfo
This package provides debug information for package %{name}.
Debug information is useful when developing applications that use this
package or when debugging this package.
%endif

%prep
%setup -T -n %{name}-%{version}-%{release} -c
%{__tar} -xo -f %{SOURCE0}
mv %{name}-%{version} %{name}-%{version}-%{efiarch}
cd %{name}-%{version}-%{efiarch}
git init
git config user.email "example@example.com"
git config user.name "rpmbuild -bp"
git add .
git commit -a -q -m "%{version} baseline."
git am --ignore-whitespace %{patches} </dev/null
git config --unset user.email
git config --unset user.name

%ifarch x86_64
cd ..
%{__tar} -xo -f %{SOURCE0}
mv %{name}-%{version} %{name}-%{version}-ia32
cd %{name}-%{version}-ia32
git init
git config user.email "example@example.com"
git config user.name "rpmbuild -bp"
git add .
git commit -a -q -m "%{version} baseline."
git am --ignore-whitespace %{patches} </dev/null
git config --unset user.email
git config --unset user.name
%endif

%build
COMMITID=$(cat %{name}-%{version}-%{efiarch}/commit)
MAKEFLAGS="RELEASE=%{release} ENABLE_HTTPBOOT=true COMMITID=${COMMITID}"
%ifarch aarch64
if [ -f "%{SOURCE1}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_CERT_FILE=%{SOURCE1}"
fi
if [ -f "%{SOURCE3}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_DBX_FILE=%{SOURCE3}"
fi
if [ -f "%{SOURCE5}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_ESL_FILE=%{SOURCE5}"
fi
%else
if [ -f "%{SOURCE1}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_CERT_FILE=%{SOURCE1}"
fi
if [ -f "%{SOURCE2}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_DBX_FILE=%{SOURCE2}"
fi
if [ -f "%{SOURCE5}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_ESL_FILE=%{SOURCE5}"
fi
%endif
cd %{name}-%{version}-%{efiarch}
make 'DEFAULT_LOADER=\\\\grub%{efiarch}.efi' ${MAKEFLAGS} shim%{efiarch}.efi mm%{efiarch}.efi fb%{efiarch}.efi

%ifarch x86_64
cd ../%{name}-%{version}-ia32
setarch linux32 -B make 'DEFAULT_LOADER=\\\\grubia32.efi' ARCH=ia32 ${MAKEFLAGS} shimia32.efi mmia32.efi fbia32.efi
cd ../%{name}-%{version}-%{efiarch}
%endif

%install
cd %{name}-%{version}-%{efiarch}
pesign -h -P -i shim%{efiarch}.efi -h > shim%{efiarch}.hash
install -D -d -m 0755 $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/
install -m 0644 shim%{efiarch}.hash $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/shim%{efiarch}.hash
for x in shim%{efiarch} mm%{efiarch} fb%{efiarch} ; do
	install -m 0644 $x.efi $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/
	install -m 0644 $x.so $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/
done

%ifarch x86_64
cd ../%{name}-%{version}-ia32
pesign -h -P -i shimia32.efi -h > shimia32.hash
install -D -d -m 0755 $RPM_BUILD_ROOT%{_datadir}/shim/ia32-%{version}-%{release}/
install -m 0644 shimia32.hash $RPM_BUILD_ROOT%{_datadir}/shim/ia32-%{version}-%{release}/shimia32.hash
for x in shimia32 mmia32 fbia32 ; do
	install -m 0644 $x.efi $RPM_BUILD_ROOT%{_datadir}/shim/ia32-%{version}-%{release}/
	install -m 0644 $x.so $RPM_BUILD_ROOT%{_datadir}/shim/ia32-%{version}-%{release}/
done
cd ../%{name}-%{version}-%{efiarch}
%endif

%ifarch x86_64
%global __debug_install_post						\
	bash %{SOURCE4}							\\\
		%{?_missing_build_ids_terminate_build:--strict-build-id}\\\
		%{?_find_debuginfo_opts} 				\\\
		"%{_builddir}/%{?buildsubdir}/%{name}-%{version}-%{efiarch}" \
	rm -f $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/*.so \
	mv debugfiles.list ../debugfiles-%{efiarch}.list		\
	cd ..								\
	cd %{name}-%{version}-ia32					\
	bash %{SOURCE4}							\\\
		%{?_missing_build_ids_terminate_build:--strict-build-id}\\\
		%{?_find_debuginfo_opts}				\\\
		"%{_builddir}/%{?buildsubdir}/%{name}-%{version}-ia32"	\
	rm -f $RPM_BUILD_ROOT%{_datadir}/shim/ia32-%{version}-%{release}/*.so \
	mv debugfiles.list ../debugfiles-ia32.list			\
	cd ..								\
	%{nil}
%else
%global __debug_install_post						\
	bash %{SOURCE4}							\\\
		%{?_missing_build_ids_terminate_build:--strict-build-id}\\\
		%{?_find_debuginfo_opts}				\\\
		"%{_builddir}/%{?buildsubdir}/%{name}-%{version}-%{efiarch}" \
	rm -f $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/*.so \
	mv debugfiles.list ../debugfiles-%{efiarch}.list		\
	cd ..								\
	%{nil}
%endif

%files -n shim-unsigned-%{efiarch}
%dir %{_datadir}/shim
%dir %{_datadir}/shim/%{efiarch}-%{version}-%{release}/
%{_datadir}/shim/%{efiarch}-%{version}-%{release}/*.efi
%{_datadir}/shim/%{efiarch}-%{version}-%{release}/*.hash

%files -n shim-unsigned-%{efiarch}-debuginfo -f debugfiles-%{efiarch}.list
%defattr(-,root,root)

%ifarch x86_64
%files -n shim-unsigned-ia32
%dir %{_datadir}/shim
%dir %{_datadir}/shim/ia32-%{version}-%{release}/
%{_datadir}/shim/ia32-%{version}-%{release}/*.efi
%{_datadir}/shim/ia32-%{version}-%{release}/*.hash

%files -n shim-unsigned-ia32-debuginfo -f debugfiles-ia32.list
%defattr(-,root,root)
%endif

%changelog
* Mon Jul 23 2018 Fabian Arrotin <arrfab@centos.org> - 12-2.el7.centos
- Added 0001-Add-vendor-esl.patch (Patrick Uiterwijk)
- Rebuilt with combined centos.esl (so new and previous crt) 

* Tue Aug 08 2017 Karanbir Singh <kbsingh@centos.org> - 12.1.el7.centos
- Rebuild with CentOS cert

* Thu Apr 27 2017 Peter Jones <pjones@redhat.com> - 12-1
- Update to 12-1 to work around a signtool.exe bug
  Related: rhbz#1445393

* Mon Apr 03 2017 Peter Jones <pjones@redhat.com> - 11-1
- Update to 11-1
  Related: rhbz#1310766
- Fix regression in PE loader
  Related: rhbz#1310766
- Fix case where BDS invokes us wrong and we exec shim again as a result
  Related: rhbz#1310766

* Tue Mar 21 2017 Peter Jones <pjones@redhat.com> - 10-1
- Update to 10-1
- Support ia32
  Resolves: rhbz#1310766
- Handle various different load option implementation differences
- TPM 1 and TPM 2 support.
- Update to OpenSSL 1.0.2k

* Mon Jun 22 2015 Peter Jones <pjones@redhat.com> - 0.9-1
- Update to 0.9-1
- Fix early call to BS->Exit()
  Resolves: rhbz#1115843
- Implement shim on aarch64
  Resolves: rhbz#1100048
  Resolves: rhbz#1190191

* Mon Jun 22 2015 Peter Jones <pjones@redhat.com> - 0.7-14
- Excise mokutil.
  Related: rhbz#1100048

* Mon Jun 22 2015 Peter Jones <pjones@redhat.com> - 0.7-13
- Do a build for Aarch64 to make the tree composable.
  Related: rhbz#1100048

* Wed Feb 25 2015 Peter Jones <pjones@redhat.com> - 0.7-10
- Fix a couple more minor bugs aavmf has found in fallback.
  Related: rhbz#1190191
- Build lib/ with the right CFLAGS
  Related: rhbz#1190191

* Tue Feb 24 2015 Peter Jones <pjones@redhat.com> - 0.7-9
- Fix aarch64 section loading.
  Related: rhbz#1190191

* Tue Sep 30 2014 Peter Jones <pjones@redhat.com> - 0.7-8
- Build -8 for arm as well.
  Related: rhbz#1100048
- out-of-bounds memory read flaw in DHCPv6 packet processing
  Resolves: CVE-2014-3675
- heap-based buffer overflow flaw in IPv6 address parsing
  Resolves: CVE-2014-3676
- memory corruption flaw when processing Machine Owner Keys (MOKs)
  Resolves: CVE-2014-3677

* Tue Sep 23 2014 Peter Jones <pjones@redhat.com> - 0.7-7
- Use the right key for ARM Aarch64.

* Sun Sep 21 2014 Peter Jones <pjones@redhat.com> - 0.7-6
- Preliminary build for ARM Aarch64.

* Tue Feb 18 2014 Peter Jones <pjones@redhat.com> - 0.7-5
- Update for production signing
  Resolves: rhbz#1064424
  Related: rhbz#1064449

* Thu Nov 21 2013 Peter Jones <pjones@redhat.com> - 0.7-4
- Make dhcpv4 paths work better when netbooting.
  Resolves: rhbz#1032583

* Thu Nov 14 2013 Peter Jones <pjones@redhat.com> - 0.7-3
- Make lockdown include UEFI and other KEK/DB entries.
  Resolves: rhbz#1030492

* Fri Nov 08 2013 Peter Jones <pjones@redhat.com> - 0.7-2
- Update lockdown to reflect SetupMode better as well
  Related: rhbz#996863

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 0.7-1
- Fix logic to handle SetupMode efi variable.
  Related: rhbz#996863

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 0.6-1
- Fix a FreePool(NULL) call on machines too old for SB

* Fri Oct 04 2013 Peter Jones <pjones@redhat.com> - 0.5-1
- Update to 0.5

* Tue Aug 06 2013 Peter Jones <pjones@redhat.com> - 0.4-3
- Build with early RHEL test keys.
  Related: rhbz#989442

* Thu Jul 25 2013 Peter Jones <pjones@redhat.com> - 0.4-2
- Fix minor RHEL 7.0 build issues
  Resolves: rhbz#978766
- Be less verbose by default

* Tue Jun 11 2013 Peter Jones <pjones@redhat.com> - 0.4-1
- Update to 0.4

* Fri Jun 07 2013 Peter Jones <pjones@redhat.com> - 0.3-2
- Require gnu-efi-3.0q for now.
- Don't allow mmx or sse during compilation.
- Re-organize this so all real signing happens in shim-signed instead.
- Split out mokutil

* Wed Dec 12 2012 Peter Jones <pjones@redhat.com> - 0.2-3
- Fix mokutil's idea of signature sizes.

* Wed Nov 28 2012 Matthew Garrett <mjg59@srcf.ucam.org> - 0.2-2
- Fix secure_mode() always returning true

* Mon Nov 26 2012 Matthew Garrett <mjg59@srcf.ucam.org> - 0.2-1
- Update shim
- Include mokutil
- Add debuginfo package since mokutil is a userspace executable

* Mon Oct 22 2012 Peter Jones <pjones@redhat.com> - 0.1-4
- Produce an unsigned shim

* Tue Aug 14 2012 Peter Jones <pjones@redhat.com> - 0.1-3
- Update how embedded cert and signing work.

* Mon Aug 13 2012 Josh Boyer <jwboyer@redhat.com> - 0.1-2
- Add patch to fix image size calculation

* Mon Aug 13 2012 Matthew Garrett <mjg@redhat.com> - 0.1-1
- initial release
