# PSPLibDoc
An attempt to document symbols of PSP modules across all firmwares.\
Page with the current NID status for each library can be found [here](https://pspdev.github.io/psplibdoc/).
<br>
 
## Usage
### Prerequisites
psp_libdoc.py and psp_print_libdoc.py require python3 with lxml module.

### Common psp_libdoc operations
 - Loading source files
    - Load one or more PSPLibDoc XML files
        - psp_libdoc.py -l input_1.xml input_2.xml input_3.xml...

    - Load one or more PSP export files
        - psp_libdoc.py -e input_1.exp input_2.exp input_3.exp...

    - Load one or more PPSSPP source files (HLEFunction arrays)
        - psp_libdoc.py -p input_1.cpp input_2.cpp input_3.cpp...

    - Combination of multiple different sources
        - psp_libdoc.py -l input_1.xml input_2.xml... -e input_1.exp input_2.exp... -p ...

 - Save a combined PSPLibDoc XML file from all loaded sources
    - psp_libdoc.py *sources* -c psp_libdoc.xml
    - save_combined.sh will create a combined PSPLibDoc file for all firmwares and modules
    - save_per_fw_version.sh will create a combined PSPLibDoc file for all firmware versions, each containing all modules

 - Save PRX modules as individual PSPLibDoc XML files from all loaded sources
    - psp_libdoc.py *sources* -s outputFolder

 - Update a PSPLibDoc XML file with known NIDs from all loaded sources
    - psp_libdoc.py *sources* -u psp_libdoc_to_update.xml
    - update_imports.sh will update the Import files for all firmwares from the combined PSPLibDoc

 - Update the PSPLibDoc XML files of all firmwares from PSP export files (*.exp)
    - Put all export files into an input folder and name them after the prx it should update
    - Example: ata.exp, sysmem.exp in inputFolder will update ata.xml and sysmem.xml across all firmwares
    - ./update_from_psp_exports.sh inputFolder

 - Export all unknown NIDs from all loaded sources
    - psp_libdoc.py *sources* -o unknown_nids.txt

 - Export all known function names from all loaded sources
    - psp_libdoc.py *sources* -k known_function_names.txt
<br>

### Common psp_print_libdoc operations
 - Print all exports of a given PRX module
    - psp_print_libdoc.py -d *directory* -e *module*
    - Example: psp_print_libdoc.py -d PSPLibDoc/1.50/ -e sysmem

 - Print all imports of a given PRX module
    - psp_print_libdoc.py -d *directory* -i *module*
    - Example: psp_print_libdoc.py -d PSPLibDoc/1.50/ -i threadman

 - Print all PRX modules exporting a given library
    - psp_print_libdoc.py -d *directory* -l *library*
    - Example: psp_print_libdoc.py -d PSPLibDoc/1.50/ -l SysMemForKernel

 - Print all PRX modules importing a given library
    - psp_print_libdoc.py -d *directory* -m *library*
    - Example: psp_print_libdoc.py -d PSPLibDoc/1.50/ -m LoadCoreForKernel
<br>

### Misc tools
 - Check NIDs which have a name attributed to them in an xml but not another one
   - check_missing_known_nids.py

 - Generate a page containing the statistics of known and unknown NIDs
   - make_statistics.py

 - Try matching NIDs before and after obfuscation using prxtool to find the closest functions
   - match-nids.py input.xml module_ver1.prx module_ver2.prx module_ver3.prx ...
   - Note that this will override previously already defined names

 - Check if the "SOURCE" field of a NID is correct
   - ./update_source.py
   - Authorized values are "matching" (NID matches the name), "previous version" (name taken from a previous version), "previous version (automated)" (same but with automated function matching) and "unknown"

## General Notes
 - psp_libdoc currently does not load or save variables (Updating a PSPLibDoc however preserves variables)
 - Updating a PSPLibDoc is based on NID only, a loaded entry with the same NID will overwrite the previous one
<br>

## Firmware Notes
 - Firmware 1.00 is an accidentally leaked pre-release firmware by Sony (also known as 1.00 Bogus)
 - Firmware 1.03 is the actual PSP Japan release firmware (VSH only reports 1.00)
 - Firmwares in the ePSPVitaLibDoc folder refer to PS Vita firmware
 - The PS Vita ePSP emulator was based on different PSP firmwares throughout its lifecycle
    - Since PS Vita ePSP 0.931 -> PSP 6.20
    - Since PS Vita ePSP 0.990 -> PSP 6.36
    - Since PS Vita ePSP 1.03 -> PSP 6.60
    - Since PS Vita ePSP 3.36 -> PSP 6.61
<br>

## Credits
A big thanks goes to
 - All original PSPLibDoc contributers
 - All PPSSPP contributers for additional user library symbols
 - All uOFW contributors for updated 6.60 and 6.61 symbols
 - artart78, Draan, efonte, GrapheneCt, sajattack, SilverSpring, zecoxao, Spenon-Dev for additional symbol sources and NIDs
 - Spenon-Dev for the original repo [here](https://github.com/Spenon-dev/PSPLibDoc)
