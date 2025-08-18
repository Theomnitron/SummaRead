import streamlit as st

head = st.markdown('<h2>Heading</h2>', icon= ':material/person:', unsafe_allow_html= True)
# body = st.markdown("""
#                     <p>
#                         A short label explaining to the user what this button is for.
#                         The label can optionally contain GitHub-flavored Markdown of the following types: Bold, Italics, Strikethroughs, Inline Code, Links, and Images.
#                         Images display like icons, with a max height equal to the font height.
#                         Unsupported Markdown elements are unwrapped so only their children (text contents) render.
#                         Display unsupported elements as literal characters by backslash-escaping them. E.g., "1\. Not an ordered list".
#                         See the body parameter of st.markdown for additional, supported Markdown directives.
#                     </p>
#                     """, unsafe_allow_html= True)
# message = st.text_area("Message", value="Lorem ipsum.\nStreamlit is cool.")
# combo = head + body

# if st.button("Prepare download"):
#     st.download_button(
#         label="Download text",
#         data=combo,
#         file_name="combo.docx",
#         on_click="ignore",
#         type="primary",
#         icon=":material/download:",
#     )
