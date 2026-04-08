import streamlit as st
import py3Dmol
import base64
import requests

# ---------------------- BACKGROUND ----------------------

def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg = get_base64("protein.jpg")

st.markdown(f"""
<style>
.stApp {{
    background-image: url("data:image/jpg;base64,{bg}");
    background-size: cover;
    background-position: center;
}}

.stApp::before {{
    content: "";
    position: fixed;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.65);
    z-index: -1;
}}

h1, h2, h3, h4, label, p {{
    color: white !important;
}}

li {{
    color: white !important;
    font-size: 16px;
}}

textarea, input {{
    color: black !important;
}}

/* ✅ FIX DROPDOWN TEXT */
div[data-baseweb="select"] span {{
    color: black !important;
}}

div[role="option"] {{
    color: black !important;
}}

/* BUTTON */
.stButton>button {{
    background-color: red;
    color: white;
    font-weight: bold;
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------- CODON TABLE ----------------------

codon_table = {
    'ATA':'I','ATC':'I','ATT':'I','ATG':'M',
    'ACA':'T','ACC':'T','ACG':'T','ACT':'T',
    'AAC':'N','AAT':'N','AAA':'K','AAG':'K',
    'AGC':'S','AGT':'S','AGA':'R','AGG':'R',
    'CTA':'L','CTC':'L','CTG':'L','CTT':'L',
    'CCA':'P','CCC':'P','CCG':'P','CCT':'P',
    'CAC':'H','CAT':'H','CAA':'Q','CAG':'Q',
    'CGA':'R','CGC':'R','CGG':'R','CGT':'R',
    'GTA':'V','GTC':'V','GTG':'V','GTT':'V',
    'GCA':'A','GCC':'A','GCG':'A','GCT':'A',
    'GAC':'D','GAT':'D','GAA':'E','GAG':'E',
    'GGA':'G','GGC':'G','GGG':'G','GGT':'G',
    'TCA':'S','TCC':'S','TCG':'S','TCT':'S',
    'TTC':'F','TTT':'F','TTA':'L','TTG':'L',
    'TAC':'Y','TAT':'Y','TAA':'_','TAG':'_',
    'TGC':'C','TGT':'C','TGA':'_','TGG':'W',
}

def translate(seq):
    protein = ""
    for i in range(0, len(seq)-2, 3):
        protein += codon_table.get(seq[i:i+3], 'X')
    return protein

def gc_content(seq):
    return (seq.count('G') + seq.count('C')) / len(seq) * 100 if len(seq) > 0 else 0

def highlight_mutation(seq, position):
    result = ""
    for i, base in enumerate(seq):
        if i == position - 1:
            result += f"<span style='color:red; font-weight:bold; background:yellow'>{base}</span>"
        else:
            result += f"<span style='color:white; font-weight:bold'>{base}</span>"
    return result

# ---------------------- MUTATION TYPE ----------------------

def classify_mutation(original_seq, mutated_seq, position):
    codon_start = ((position - 1) // 3) * 3

    orig_codon = original_seq[codon_start:codon_start+3]
    mut_codon = mutated_seq[codon_start:codon_start+3]

    orig_aa = codon_table.get(orig_codon, 'X')
    mut_aa = codon_table.get(mut_codon, 'X')

    if orig_aa == mut_aa:
        return "Silent Mutation"
    elif mut_aa == "_":
        return "Nonsense Mutation"
    else:
        return "Missense Mutation"

# ---------------------- STRUCTURE ----------------------

def predict_structure(protein_seq):
    url = "https://api.esmatlas.com/foldSequence/v1/pdb/"
    try:
        res = requests.post(url, data=protein_seq, timeout=20)
        if res.status_code == 200:
            return res.text
    except:
        return None

def show_structure(pdb_data, pos):
    view = py3Dmol.view()
    view.addModel(pdb_data, "pdb")
    view.setStyle({'cartoon': {'color': 'spectrum'}})
    view.addStyle({'resi': pos}, {'stick': {'color': 'red'}})
    view.zoomTo()
    return view._make_html()

def fallback_structure(pos):
    view = py3Dmol.view(query='pdb:1CRN')
    view.setStyle({'cartoon': {'color': 'spectrum'}})
    view.addStyle({'resi': pos}, {'stick': {'color': 'red'}})
    view.zoomTo()
    return view._make_html()

# ---------------------- UI ----------------------

st.title("Genome Editor Tool")

# ---------------------- ABOUT ----------------------

with st.expander("About Tool"):
    st.write("""
This tool allows users to perform genome editing by introducing point mutations 
in a DNA sequence.

Features:
- DNA mutation simulation
- Mutation classification (Silent, Missense, Nonsense)
- Protein translation
- GC content analysis
- Real-time structure prediction (ESMFold)
- Mutation visualization on 3D structure
""")

# ---------------------- INPUT ----------------------

seq = st.text_area("Enter DNA Sequence").upper()
position = st.number_input("Position to Mutate (1-based)", min_value=1)
new_base = st.selectbox("New Base", ["A", "T", "G", "C"])

# ---------------------- ACTION ----------------------

if st.button("Apply Mutation"):

    if not seq:
        st.warning("Enter sequence")

    elif position > len(seq):
        st.warning("Invalid position")

    else:
        mutated_seq = list(seq)
        mutated_seq[position-1] = new_base
        mutated_seq = "".join(mutated_seq)

        st.subheader("Mutated Sequence")
        st.markdown(highlight_mutation(mutated_seq, position), unsafe_allow_html=True)

        st.subheader("Protein Output")
        protein = translate(mutated_seq)
        st.write(protein)

        st.subheader("GC Content")
        st.write(gc_content(mutated_seq))

        # ✅ Mutation type
        st.subheader("Mutation Type")
        mutation_type = classify_mutation(seq, mutated_seq, position)
        st.write(mutation_type)

        st.subheader("Predicted 3D Structure")

        protein_pos = (position - 1) // 3 + 1

        if len(protein) < 30:
            st.warning("Protein too short → showing default structure")
            html = fallback_structure(protein_pos)
        else:
            with st.spinner("Predicting structure..."):
                pdb = predict_structure(protein)

            if pdb:
                html = show_structure(pdb, protein_pos)
            else:
                st.warning("Prediction failed → showing default structure")
                html = fallback_structure(protein_pos)

        st.components.v1.html(html, height=400)