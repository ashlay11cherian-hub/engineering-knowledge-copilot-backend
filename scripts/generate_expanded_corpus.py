import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path("backend/data")

REQUIRED_FIELDS = {
    "document_id",
    "title",
    "source_type",
    "department",
    "classification",
    "allowed_roles",
    "revision",
    "content",
    "program_id",
    "authority_rank",
    "document_status",
}

VALID_CLASSIFICATIONS = {
    "internal",
    "confidential",
    "restricted",
    "highly_restricted",
}

VALID_ROLES = {
    "engineer",
    "program_manager",
    "hr",
    "executive",
}

VALID_STATUSES = {
    "current",
    "superseded",
}


def doc(
    document_id,
    title,
    source_type,
    department,
    classification,
    allowed_roles,
    revision,
    content,
    program_id,
    authority_rank,
    document_status="current",
):
    return {
        "document_id": document_id,
        "title": title,
        "source_type": source_type,
        "department": department,
        "classification": classification,
        "allowed_roles": allowed_roles,
        "revision": revision,
        "content": content,
        "program_id": program_id,
        "authority_rank": authority_rank,
        "document_status": document_status,
    }


NEW_DOCUMENTS = [

    # ==========================================================
    # GEN3-WLC — Automotive Wireless Charging
    # +3 documents
    # ==========================================================

    doc(
        "REQ-119",
        "Gen-3 Wireless Charger Thermal Design Requirements",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "2.0",
        (
            "The Gen-3 wireless charging system shall maintain normal operation "
            "through the defined high-temperature operating envelope without thermal "
            "shutdown. Mechanical stack-up shall control transmitter coil location "
            "relative to the receiver interface. DV verification shall include "
            "worst-case alignment tolerance, elevated ambient temperature, and "
            "continuous charging operation."
        ),
        "GEN3-WLC",
        85,
    ),

    doc(
        "MFG-061",
        "Gen-3 Wireless Charger DV2 Manufacturing Readiness Review",
        "manufacturing_readiness_report",
        "operations",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "DV2 manufacturing readiness confirmed updated locating fixtures, "
            "revised coil-position inspection criteria, and TIM-07 work instructions. "
            "The production team added an alignment verification checkpoint before "
            "final housing closure. Pilot builds showed stable assembly repeatability "
            "with no thermal shutdowns attributed to coil placement."
        ),
        "GEN3-WLC",
        70,
    ),

    doc(
        "SUP-044",
        "Gen-3 Coil Alignment Supplier Capability Review",
        "supplier_quality_report",
        "supply_chain",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Supplier capability review confirmed that the revised locating-pin and "
            "coil-carrier tolerances can be maintained under the updated drawing. "
            "The supplier committed to additional dimensional checks during ramp and "
            "a capability study on the coil-location critical characteristics before "
            "production release."
        ),
        "GEN3-WLC",
        75,
    ),

    # ==========================================================
    doc(
        "SPEC-120",
        "Gen-3 External Surface Temperature Limit - Rev A",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "A",
        (
            "The maximum allowable external surface temperature for the "
            "Gen-3 wireless charging module shall not exceed 60 degrees "
            "Celsius during normal operation under the defined thermal "
            "validation conditions."
        ),
        "GEN3-WLC",
        90,
        "current",
    ),

    doc(
        "SPEC-121",
        "Gen-3 External Surface Temperature Limit - Rev B",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "B",
        (
            "The maximum allowable external surface temperature for the "
            "Gen-3 wireless charging module shall not exceed 65 degrees "
            "Celsius during normal operation under the defined thermal "
            "validation conditions."
        ),
        "GEN3-WLC",
        90,
        "current",
    ),

    # TELEMATICS-X
    # +7 documents
    # ==========================================================

    doc(
        "REQ-301",
        "Telematics-X Connectivity and Recovery Requirements",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Telematics-X shall maintain LTE and GNSS connectivity across the defined "
            "vehicle operating environment. Following a temporary network interruption, "
            "the unit shall automatically recover connectivity without requiring an "
            "ignition cycle. Antenna grounding and RF performance shall be verified "
            "across production tolerance conditions."
        ),
        "TELEMATICS-X",
        85,
    ),

    doc(
        "EVT-312",
        "Telematics-X EVT Connectivity Test Report",
        "prototype_test_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "EVT testing reproduced intermittent LTE signal degradation in 3 of 12 "
            "units during vibration and elevated-temperature testing. GNSS remained "
            "functional. Investigation was opened to determine whether the failure "
            "originated in antenna grounding, shielding, or modem firmware."
        ),
        "TELEMATICS-X",
        65,
    ),

    doc(
        "NOTE-318",
        "Preliminary Telematics-X RF Investigation Note",
        "informal_engineering_note",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "0.2",
        (
            "The initial engineering hypothesis attributed the LTE degradation to "
            "inconsistent RF shield adhesive coverage near the modem. This conclusion "
            "was preliminary. Later controlled testing did not reproduce a correlation "
            "with adhesive coverage and superseded this hypothesis."
        ),
        "TELEMATICS-X",
        20,
        "superseded",
    ),

    doc(
        "JIRA-317",
        "Telematics-X Intermittent Network Drop Investigation",
        "jira_ticket",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Root-cause testing confirmed excessive variation in the antenna grounding "
            "spring contact height. Reduced contact pressure increased RF loss during "
            "vibration. The issue reproduced across tolerance-stack extremes and was "
            "not caused by RF shield adhesive coverage."
        ),
        "TELEMATICS-X",
        60,
    ),

    doc(
        "ECR-319",
        "Telematics-X Antenna Grounding Revision",
        "engineering_change_request",
        "engineering",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Approved change increases nominal antenna grounding spring height, tightens "
            "contact-height tolerance, and adds an assembly verification requirement. "
            "The change was approved for the next design-validation build following "
            "root-cause confirmation of insufficient grounding contact pressure."
        ),
        "TELEMATICS-X",
        100,
    ),

    doc(
        "PLM-TX-RB",
        "Telematics-X Released Configuration Revision B",
        "plm_record",
        "engineering",
        "confidential",
        ["program_manager"],
        "B",
        (
            "Released Revision B incorporates the revised antenna grounding spring, "
            "updated contact-height tolerance, and inspection characteristic. The "
            "configuration supersedes the EVT hardware configuration and is the "
            "approved baseline for subsequent validation."
        ),
        "TELEMATICS-X",
        95,
    ),

    doc(
        "FIN-320",
        "Telematics-X Unit Economics",
        "financial_report",
        "finance",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "The current Telematics-X manufacturing cost model estimates a unit cost "
            "of $68 at planned production volume. The program target gross margin is "
            "29 percent. Cost-down activity is focused on modem sourcing, enclosure "
            "machining, and antenna assembly."
        ),
        "TELEMATICS-X",
        90,
    ),

    # ==========================================================
    # WEARABLE-ORBIT
    # +8 documents
    # ==========================================================

    doc(
        "REQ-401",
        "Orbit Wearable Battery and Sensor Requirements",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Orbit shall achieve at least five days of typical-use battery life and "
            "maintain continuous optical heart-rate measurement during normal exercise. "
            "Sensor performance shall be validated across representative skin-contact "
            "conditions, motion profiles, temperature, and battery state."
        ),
        "WEARABLE-ORBIT",
        85,
    ),

    doc(
        "EVT-402",
        "Orbit EVT Battery Life Test Report",
        "prototype_test_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "EVT battery testing achieved 4.3 days of typical simulated use, below the "
            "five-day requirement. Analysis identified elevated idle current from the "
            "prototype display driver and debug logging. Firmware optimization and a "
            "revised display power state were assigned before DVT."
        ),
        "WEARABLE-ORBIT",
        65,
    ),

    doc(
        "NOTE-404",
        "Preliminary Orbit Optical Sensor Dropout Note",
        "informal_engineering_note",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "0.1",
        (
            "Early bench review suggested that optical sensor dropouts during running "
            "were caused by contamination on the optical window. Cleaning improved one "
            "sample, but subsequent controlled testing showed that contamination was "
            "not the dominant failure mechanism. This note is superseded."
        ),
        "WEARABLE-ORBIT",
        20,
        "superseded",
    ),

    doc(
        "JIRA-403",
        "Orbit Exercise Heart-Rate Dropout Investigation",
        "jira_ticket",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Investigation confirmed that sensor dropouts were driven by insufficient "
            "and inconsistent skin contact during high-motion exercise. Mechanical "
            "tolerance in the sensor dome and strap interface reduced optical coupling "
            "on worst-case units. Window contamination was not the primary cause."
        ),
        "WEARABLE-ORBIT",
        60,
    ),

    doc(
        "DVT-405",
        "Orbit DVT Optical Sensor Validation Report",
        "validation_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "DVT validation of the revised sensor dome and strap interface met the "
            "heart-rate continuity requirement across the defined exercise profiles. "
            "The revised geometry maintained improved skin contact and eliminated the "
            "dropout pattern observed in EVT."
        ),
        "WEARABLE-ORBIT",
        80,
    ),

    doc(
        "ECR-406",
        "Orbit Optical Stack Mechanical Update",
        "engineering_change_request",
        "engineering",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Approved engineering change revises sensor-dome height, strap-interface "
            "geometry, and optical stack compression limits. The change addresses the "
            "confirmed high-motion sensor dropout root cause and became effective for "
            "DVT build hardware."
        ),
        "WEARABLE-ORBIT",
        100,
    ),

    doc(
        "PVT-407",
        "Orbit PVT Manufacturing Yield Report",
        "manufacturing_readiness_report",
        "operations",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "PVT first-pass yield reached 94 percent. The largest remaining losses were "
            "cosmetic enclosure defects and adhesive placement variation. Optical sensor "
            "assembly yield was stable after implementation of the revised fixture and "
            "dome-height inspection."
        ),
        "WEARABLE-ORBIT",
        70,
    ),

    doc(
        "FIN-408",
        "Orbit Wearable Unit Economics",
        "financial_report",
        "finance",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Orbit estimated manufacturing cost is $51 per unit at planned volume. "
            "Target gross margin is 42 percent. Primary cost drivers are the display, "
            "optical sensor module, battery, and machined enclosure."
        ),
        "WEARABLE-ORBIT",
        90,
    ),

    # ==========================================================
    # SMARTGLASS-NOVA
    # +8 documents
    # ==========================================================

    doc(
        "REQ-501",
        "Nova Smart Glasses Thermal Comfort Requirements",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Nova temple surface temperature shall remain within the user-comfort limit "
            "during continuous camera, display, and wireless operation. Thermal "
            "validation shall include worst-case ambient temperature, charging state, "
            "high compute load, and tolerance-stack conditions."
        ),
        "SMARTGLASS-NOVA",
        85,
    ),

    doc(
        "EVT-502",
        "Nova EVT Temple Thermal Test Report",
        "prototype_test_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "EVT testing identified a right-temple hotspot during simultaneous camera "
            "capture and display operation. Peak surface temperature exceeded the "
            "comfort target on four units. The issue was escalated for mechanical and "
            "thermal root-cause investigation."
        ),
        "SMARTGLASS-NOVA",
        65,
    ),

    doc(
        "NOTE-503",
        "Preliminary Nova Processor Power Hypothesis",
        "informal_engineering_note",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "0.1",
        (
            "The initial hypothesis attributed the Nova temple hotspot primarily to "
            "higher-than-expected processor power consumption. Later instrumentation "
            "showed processor power was within budget and that the dominant issue was "
            "thermal-spreader compression caused by flex-cable routing. Superseded."
        ),
        "SMARTGLASS-NOVA",
        20,
        "superseded",
    ),

    doc(
        "JIRA-504",
        "Nova Right-Temple Hotspot Investigation",
        "jira_ticket",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Root-cause investigation confirmed that display flex routing compressed "
            "and locally lifted the graphite heat spreader, increasing thermal "
            "resistance between the processor region and temple frame. Processor power "
            "remained within the approved budget."
        ),
        "SMARTGLASS-NOVA",
        60,
    ),

    doc(
        "ECR-505",
        "Nova Thermal Spreader and Flex Routing Revision",
        "engineering_change_request",
        "engineering",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Approved change reroutes the display flex, adds a controlled clearance "
            "feature, and revises graphite-spreader retention. The change was approved "
            "to remove local spreader deformation and reduce right-temple surface "
            "temperature."
        ),
        "SMARTGLASS-NOVA",
        100,
    ),

    doc(
        "DVT-506",
        "Nova Hinge Durability Validation Report",
        "validation_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Nova DVT hinge testing completed the required open-close cycling without "
            "structural fracture. Two early samples showed torque drift but remained "
            "functional. Updated lubrication control reduced torque variation in the "
            "final validation population."
        ),
        "SMARTGLASS-NOVA",
        80,
    ),

    doc(
        "SUP-507",
        "Nova Optics Supplier Qualification Report",
        "supplier_quality_report",
        "supply_chain",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "The primary waveguide supplier passed dimensional, optical-efficiency, "
            "cosmetic, and environmental qualification for the current Nova design. "
            "Production approval is conditional on maintaining the agreed incoming "
            "inspection and lot-traceability controls."
        ),
        "SMARTGLASS-NOVA",
        75,
    ),

    doc(
        "FIN-508",
        "Nova Smart Glasses Unit Economics",
        "financial_report",
        "finance",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Nova estimated manufacturing cost is $214 per unit at initial production "
            "volume. Optics, processor, cameras, and custom mechanical assemblies are "
            "the largest cost contributors. The current cost-reduction plan prioritizes "
            "optics yield and mechanical part consolidation."
        ),
        "SMARTGLASS-NOVA",
        90,
    ),

    # ==========================================================
    # EARBUDS-PULSE
    # +7 documents
    # ==========================================================

    doc(
        "REQ-601",
        "Pulse Earbuds Acoustic and ANC Requirements",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Pulse shall meet the defined active-noise-cancellation attenuation and "
            "voice-call quality targets across the supported fit range. Acoustic "
            "validation shall include wind, speech, music, transportation noise, "
            "microphone tolerance, and vent variation."
        ),
        "EARBUDS-PULSE",
        85,
    ),

    doc(
        "EVT-602",
        "Pulse Earbuds EVT Battery Test Report",
        "prototype_test_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "EVT battery testing achieved 6.6 hours of continuous playback with ANC "
            "enabled against a seven-hour target. Power profiling identified excessive "
            "idle microphone processing between audio events. Firmware optimization "
            "was scheduled before DVT."
        ),
        "EARBUDS-PULSE",
        65,
    ),

    doc(
        "NOTE-603",
        "Preliminary Pulse Wind Noise Investigation Note",
        "informal_engineering_note",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "0.1",
        (
            "The first investigation associated wind-noise complaints with microphone "
            "mesh variation. Controlled builds using alternate meshes did not eliminate "
            "the issue. Later acoustic testing identified vent-cavity resonance as the "
            "dominant mechanism, superseding this note."
        ),
        "EARBUDS-PULSE",
        20,
        "superseded",
    ),

    doc(
        "JIRA-604",
        "Pulse ANC Wind Noise Root Cause Investigation",
        "jira_ticket",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Acoustic chamber testing confirmed that the housing vent cavity produced "
            "a resonance under cross-wind conditions, coupling energy into the external "
            "ANC microphone. Microphone mesh variation affected magnitude but was not "
            "the primary root cause."
        ),
        "EARBUDS-PULSE",
        60,
    ),

    doc(
        "ECR-605",
        "Pulse Acoustic Vent Geometry Revision",
        "engineering_change_request",
        "engineering",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Approved change revises acoustic vent cross-section and internal cavity "
            "volume to reduce wind-induced resonance. Updated ANC calibration values "
            "were released with the mechanical change for DVT verification."
        ),
        "EARBUDS-PULSE",
        100,
    ),

    doc(
        "PVT-606",
        "Pulse Charging Case PVT Yield Report",
        "manufacturing_readiness_report",
        "operations",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Charging-case PVT first-pass yield reached 96 percent. Main losses were "
            "cosmetic scratches and pogo-pin seating variation. A revised assembly "
            "fixture reduced pogo-pin seating defects during the final PVT run."
        ),
        "EARBUDS-PULSE",
        70,
    ),

    doc(
        "FIN-607",
        "Pulse Earbuds Unit Economics",
        "financial_report",
        "finance",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Pulse estimated combined earbuds and charging-case manufacturing cost is "
            "$63 per set at planned volume. Primary cost drivers are the audio SoCs, "
            "batteries, microphones, drivers, and charging-case electronics."
        ),
        "EARBUDS-PULSE",
        90,
    ),

    # ==========================================================
    # SMARTHOME-HALO
    # +6 documents
    # ==========================================================

    doc(
        "REQ-701",
        "Halo Smart Home Hub Power and Connectivity Requirements",
        "requirements_specification",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Halo shall maintain Wi-Fi connectivity and recover automatically after "
            "brief input-power disturbances. The hub shall not enter an unrecoverable "
            "boot loop under the defined adapter-voltage and household brownout "
            "conditions."
        ),
        "SMARTHOME-HALO",
        85,
    ),

    doc(
        "EVT-702",
        "Halo EVT Brownout Test Report",
        "prototype_test_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "EVT brownout testing reproduced repeated reboot behavior when input voltage "
            "recovered slowly through the minimum operating range. Five of ten units "
            "entered multiple reset cycles before eventually recovering."
        ),
        "SMARTHOME-HALO",
        65,
    ),

    doc(
        "NOTE-703",
        "Preliminary Halo AC Adapter Investigation Note",
        "informal_engineering_note",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "0.1",
        (
            "Initial troubleshooting suspected excessive output droop from the AC adapter "
            "as the primary cause of repeated Halo resets. Adapter substitution changed "
            "the timing but did not eliminate the failure. Later investigation showed "
            "the primary cause was on the hub power rail. Superseded."
        ),
        "SMARTHOME-HALO",
        20,
        "superseded",
    ),

    doc(
        "JIRA-704",
        "Halo Brownout Reboot Root Cause Investigation",
        "jira_ticket",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Root-cause investigation found insufficient hold-up capacitance on the "
            "3.3-volt rail combined with the PMIC undervoltage reset threshold. During "
            "slow input-voltage recovery the processor repeatedly crossed the reset "
            "threshold. The AC adapter was not the primary cause."
        ),
        "SMARTHOME-HALO",
        60,
    ),

    doc(
        "ECR-705",
        "Halo Power Rail Brownout Revision",
        "engineering_change_request",
        "engineering",
        "confidential",
        ["program_manager"],
        "1.0",
        (
            "Approved change increases 3.3-volt rail bulk capacitance and updates the "
            "PMIC reset configuration. Validation is required across minimum adapter "
            "voltage, slow recovery, and repeated brownout cycles before release."
        ),
        "SMARTHOME-HALO",
        100,
    ),

    doc(
        "CERT-706",
        "Halo Regulatory and Release Verification Report",
        "certification_report",
        "engineering",
        "internal",
        ["engineer", "program_manager"],
        "1.0",
        (
            "Halo completed the planned electrical safety, EMC, and wireless regulatory "
            "verification for the release configuration. Release testing used the "
            "updated power-rail design and approved production firmware baseline."
        ),
        "SMARTHOME-HALO",
        88,
    ),
]


def validate_document(document):
    from backend.src.document_validation import (
        validate_document as central_validate_document,
    )

    return central_validate_document(document)

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if len(NEW_DOCUMENTS) != 41:
        raise RuntimeError(
            f"Expected 41 new documents, found {len(NEW_DOCUMENTS)}"
        )

    ids = [
        document["document_id"]
        for document in NEW_DOCUMENTS
    ]

    if len(ids) != len(set(ids)):
        raise RuntimeError(
            "Duplicate document IDs exist inside new corpus."
        )

    existing_ids = set()

    for path in DATA_DIR.glob("*.json"):
        existing = json.loads(path.read_text())
        existing_ids.add(existing["document_id"])

    collisions = (
        existing_ids
        & set(ids)
    )

    if collisions:
        raise RuntimeError(
            f"New IDs collide with existing documents: {sorted(collisions)}"
        )

    for document in NEW_DOCUMENTS:
        validate_document(document)

        output_path = (
            DATA_DIR
            / f"{document['document_id']}.json"
        )

        output_path.write_text(
            json.dumps(
                document,
                indent=2,
            )
            + "\n"
        )

    all_docs = []

    for path in sorted(DATA_DIR.glob("*.json")):
        all_docs.append(
            json.loads(
                path.read_text()
            )
        )

    print("\nSUCCESS: synthetic corpus expanded.")
    print("New documents:", len(NEW_DOCUMENTS))
    print("Total documents:", len(all_docs))

    print("\nPROGRAM COUNTS:")
    print(
        Counter(
            document["program_id"]
            for document in all_docs
        )
    )

    print("\nSTATUS COUNTS:")
    print(
        Counter(
            document["document_status"]
            for document in all_docs
        )
    )

    print("\nCLASSIFICATION COUNTS:")
    print(
        Counter(
            document["classification"]
            for document in all_docs
        )
    )


if __name__ == "__main__":
    main()
