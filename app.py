from datetime import datetime
import os
from io import BytesIO
import base64
from PIL import Image
import numpy as np
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from xhtml2pdf import pisa

st.set_page_config(
    page_title="KARE-Immobilien Ordnungs- & Verstoßprotokoll",
    page_icon="⚠️",
    layout="wide",
)

st.title("KARE-Immobilien – Ordnungs- & Verstoßprotokoll")
st.markdown(
    "Dokumentation von Verstößen gegen die Hausordnung oder Mängeln im "
    "Gemeinschaftseigentum mit Fotodokumentation, Fristsetzung und Unterschrift."
)

with st.form("verstoss_form"):
  st.header("1. Stammdaten & Objekt")
  col1, col2 = st.columns(2)
  with col1:
    objekt_adresse = st.text_input(
        "Objektadresse / Liegenschaft", "Talstr. 32, 07545 Gera"
    )
    betroffene_partei = st.text_input(
        "Betroffene Partei / Mieter (falls bekannt)", "Unbekannt / Allgemein"
    )
    einheit = st.text_input(
        "Wohnungs- / Einheitennummer (optional)", "Flur / Treppenhaus"
    )
  with col2:
    datum = st.date_input("Datum der Feststellung", datetime.now())
    bearbeiter = st.text_input(
        "Erfasst durch (KARE-Immobilien)", "KARE-Immobilien"
    )
    verstoss_kategorie = st.selectbox(
        "Art des Verstoßes / Vorkommnisses",
        [
            "Unzulässig abgestellte Gegenstände (Flur/Fluchtwege)",
            "Müll / Sperrmüll / Falsche Mülltrennung",
            "Ruhestörung / Lärmbelästigung",
            "Beschädigung am Gemeinschaftseigentum",
            "Hausmüll / Verschmutzung im Außenbereich",
            "Unberechtigte Tierhaltung",
            "Sonstiger Verstoß gegen die Hausordnung",
        ],
    )

  st.header("2. Genaue Beschreibung des Verstoßes")
  beschreibung = st.text_area(
      "Sachverhalt / Details",
      placeholder=(
          "z.B. Im 2. Obergeschoss stehen dauerhaft mehrere Kartons und ein"
          " Schuhregal im notwendigen Fluchtweg..."
      ),
  )

  col_mass, col_frist = st.columns(2)
  with col_mass:
    massnahme = st.text_input(
        "Geforderte Maßnahme",
        "Gegenstände unverzüglich (bis zum Fristdatum) entfernen.",
    )
  with col_frist:
    frist = st.date_input(
        "Frist zur Beseitigung / Stellungnahme", datetime.now()
    )

  st.header("3. Fotodokumentation")
  uploaded_files = st.file_uploader(
      "Beweisfotos hochladen (PNG, JPG, JPEG)",
      type=["png", "jpg", "jpeg"],
      accept_multiple_files=True,
  )

  protokoll_bestätigt = st.checkbox(
      "Hiermit wird die Richtigkeit der Feststellung bestätigt."
  )

  submit_button = st.form_submit_button(
      label="Verstoßprotokoll als PDF generieren"
  )

st.header("4. Digitale Signaturen")
col_sig_info1, col_sig_info2 = st.columns(2)
with col_sig_info1:
  st.write("**Unterschrift Verursacher / Mieter (optional)**")
  canvas_mieter = st_canvas(
      fill_color="rgba(255, 255, 255, 0)",
      stroke_width=2,
      stroke_color="#000000",
      background_color="#ffffff",
      height=130,
      width=350,
      drawing_mode="freedraw",
      update_streamlit=True,
      return_image_data=True,
      key="canvas_mieter_verstoss",
  )
  if canvas_mieter.image_data is not None and np.any(
      canvas_mieter.image_data[:, :, 3] > 0
  ):
    st.session_state["saved_mieter_sig_v"] = canvas_mieter.image_data

with col_sig_info2:
  st.write("**Unterschrift KARE-Immobilien**")
  canvas_kare = st_canvas(
      fill_color="rgba(255, 255, 255, 0)",
      stroke_width=2,
      stroke_color="#000000",
      background_color="#ffffff",
      height=130,
      width=350,
      drawing_mode="freedraw",
      update_streamlit=True,
      return_image_data=True,
      key="canvas_kare_verstoss",
  )
  if canvas_kare.image_data is not None and np.any(
      canvas_kare.image_data[:, :, 3] > 0
  ):
    st.session_state["saved_kare_sig_v"] = canvas_kare.image_data

if submit_button:
  if not protokoll_bestätigt:
    st.error(
        "Bitte bestätige das Protokoll über die Checkbox, bevor du das PDF"
        " generierst."
    )
  else:
    images_html = ""
    if uploaded_files:
      images_html = "<h3>Fotodokumentation</h3><div class='photo-grid'>"
      for idx, file in enumerate(uploaded_files):
        img = Image.open(file)
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
          img = img.convert("RGB")

        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        images_html += f"""
                <div class='photo-box'>
                    <img src='data:image/jpeg;base64,{img_str}' style='width:100%; max-height:180px; object-fit:cover; border-radius:4px;'/>
                    <p style='font-size:9pt; color:#555; text-align:center; margin-top:4px;'>Foto {idx+1}: {file.name}</p>
                </div>
                """
      images_html += "</div>"


    def get_sig_base64(state_key):
      if (
          state_key in st.session_state
          and st.session_state[state_key] is not None
      ):
        img_data = st.session_state[state_key].astype("uint8")
        pil_img = Image.fromarray(img_data, mode="RGBA")
        background = Image.new("RGB", pil_img.size, (255, 255, 255))
        background.paste(pil_img, mask=pil_img.split()[3])

        buffered = BytesIO()
        background.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
      return None


    sig_str1 = get_sig_base64("saved_mieter_sig_v")
    sig_str2 = get_sig_base64("saved_kare_sig_v")

    sig_mieter_html = (
        f"<img src='data:image/png;base64,{sig_str1}'"
        " style='max-height:55px; display:block; margin-bottom:2px;'/><br>"
        if sig_str1
        else "<br><br>"
    )
    sig_mieter_html += (
        "____________________________________<br>Mieter / Verursacher"
    )

    sig_kare_html = (
        f"<img src='data:image/png;base64,{sig_str2}'"
        " style='max-height:55px; display:block; margin-bottom:2px;'/><br>"
        if sig_str2
        else "<br><br>"
    )
    sig_kare_html += "____________________________________<br>KARE-Immobilien"

    html_content = f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 15mm;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                color: #333333;
                line-height: 1.4;
                font-size: 10pt;
                margin: 0;
                padding: 0;
            }}
            .header {{
                border-bottom: 2px solid #b91c1c;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                color: #b91c1c;
                font-size: 20pt;
                margin: 0 0 5px 0;
            }}
            .header p {{
                margin: 0;
                color: #555;
                font-size: 9pt;
            }}
            h2 {{
                color: #b91c1c;
                font-size: 12pt;
                border-bottom: 1px solid #cbd5e1;
                padding-bottom: 4px;
                margin-top: 15px;
                margin-bottom: 8px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 10px;
            }}
            th, td {{
                padding: 5px 8px;
                border: 1px solid #cbd5e1;
                vertical-align: top;
            }}
            th {{
                background-color: #fef2f2;
                color: #b91c1c;
                text-align: left;
                width: 30%;
            }}
            td {{
                width: 70%;
            }}
            .photo-grid {{
                width: 100%;
                margin-top: 10px;
            }}
            .photo-box {{
                width: 48%;
                display: inline-block;
                border: 1px solid #cbd5e1;
                padding: 5px;
                background: #f8fafc;
                margin-bottom: 10px;
                vertical-align: top;
            }}
            .signature-section {{
                margin-top: 25px;
            }}
            .sig-box {{
                width: 45%;
                display: inline-block;
                margin-top: 20px;
                text-align: center;
                vertical-align: top;
            }}
        </style>
        </head>
        <body>
            <div class="header">
                <h1>KARE-Immobilien</h1>
                <p>Talstr. 32, 07545 Gera | Tel.: 0365 / 800 49 37 | E-Mail: Info@KARE-Immobilien.de</p>
                <h2 style="border:none; color:#0f172a; margin-top:10px; font-size:15pt;">Ordnungs- und Verstoßprotokoll</h2>
            </div>

            <h2>1. Stammdaten & Objekt</h2>
            <table>
                <tr><th>Objektadresse</th><td>{objekt_adresse}</td></tr>
                <tr><th>Betroffene Partei</th><td>{betroffene_partei} (Einheit: {einheit})</td></tr>
                <tr><th>Feststellungsdatum</th><td>{datum.strftime('%d.%m.%Y')}</td></tr>
                <tr><th>Erfasst durch</th><td>{bearbeiter}</td></tr>
                <tr><th>Art des Verstoßes</th><td>{verstoss_kategorie}</td></tr>
            </table>

            <h2>2. Sachverhalt & Maßnahmen</h2>
            <table>
                <tr><th>Beschreibung</th><td>{beschreibung}</td></tr>
                <tr><th>Geforderte Maßnahme</th><td>{massnahme}</td></tr>
                <tr><th>Fristsetzung</th><td><b>{frist.strftime('%d.%m.%Y')}</b></td></tr>
            </table>

            {images_html}

            <div class="signature-section">
                <p style="margin-bottom:15px; font-size:9pt;">Dokumentation des festgestellten Zustands bzw. Verstoßes gegen die Hausordnung.</p>
                <div style="width: 100%;">
                    <div class="sig-box" style="float: left;">
                        {sig_mieter_html}
                    </div>
                    <div class="sig-box" style="float: right;">
                        {sig_kare_html}
                    </div>
                </div>
                <div style="clear: both;"></div>
            </div>
        </body>
        </html>
        """

    pdf_path = "verstoss_protokoll.pdf"
    with open(pdf_path, "wb") as pdf_file:
      pisa.CreatePDF(html_content, dest=pdf_file)

    with open(pdf_path, "rb") as pdf_file:
      PDFbyte = pdf_file.read()

    st.success("Verstoßprotokoll erfolgreich als PDF erstellt!")

    safe_einheit = (
        "".join(c for c in einheit if c.isalnum() or c in (" ", "_", "-"))
        .strip()
        .replace(" ", "_")
    )
    st.download_button(
        label="📄 Verstoßprotokoll als PDF herunterladen",
        data=PDFbyte,
        file_name=f"Verstoss_{datum.strftime('%Y%m%d')}_{safe_einheit}.pdf",
        mime="application/pdf",
    )
