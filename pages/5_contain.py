import streamlit as st

st.markdown("""
            <style>
                .adj{
                    font-family: 'Open-Dyslexic', sans-serif !important;
                    font-size: 15px !important;
                    line-height: 2rem;
                    letter-spacing: 0.5px;
                }
            </style>
            """, unsafe_allow_html= True)

st.title("Hello There!")
st.write('---')
st.write("""
        <p class= adj>
            Pocahontas, born around 1596, was a Native American woman from the Powhatan tribe in Virginia.
            She is famously known for her interactions with the English colonists at Jamestown.
            While popular culture often depicts a romantic relationship with John Smith, historians debate the specifics of their interactions, suggesting a more complex dynamic involving diplomacy, cultural exchange, and potential conflict.
            Later, she was captured, converted to Christianity, and married John Rolfe, an English tobacco planter, and traveled to England, where she became a celebrity.
            She died in England in 1617, at the young age of 20 or 21.
            She is famously known for her interactions with the English colonists at Jamestown.
            While popular culture often depicts a romantic relationship with John Smith, historians debate the specifics of their interactions, suggesting a more complex dynamic involving diplomacy, cultural exchange, and potential conflict. 
         </p>
        """, unsafe_allow_html= True)
st.markdown(f'''
                <ul class='outline-summary'>
                    <li>She died in England in 1617, at the young age of 20 or 21.</li>
                    <li>he is famously known for her interactions with the English colonists at Jamestown.</li>
                    <li>She died in England in 1617, at the young age of 20 or 21.</li>
                    <li>he is famously known for her interactions with the English colonists at Jamestown.</li>
                    <li>She died in England in 1617, at the young age of 20 or 21.</li>
                    <li>he is famously known for her interactions with the English colonists at Jamestown.</li>
                </ul>
                ''',
            unsafe_allow_html=True)