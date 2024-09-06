import streamlit as st

def main():
    st.markdown("<h1 style='color: #00fecd; font-size: 35px; text-align: center; margin-left: 30px; '>DEVELOPERS</h1>", unsafe_allow_html=True)

    def member(image, name):
        st.markdown(
            f'''
            <div style="text-align: center; margin: auto;">
                <img src="./app/static/{image}" style="margin-right: 50px; margin: 5px; padding: 2px; border: 3px solid #00fecd; border-radius: 100%; max-width: 100%; height: auto; max-height: 150px; box-shadow: 0 4px 8px green">
                <h1 style='margin-top: -20px; margin-left: 20px; text-align: center; font-weight: normal; font-size: 15px; max-width: 100%; height: auto;'>{name}</h1>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    cols = st.columns(4)

    with cols[0]:  
        image = 'nico.png'
        name = 'NICO'
        member(image, name)

    with cols[1]: 
        image = 'kurt.jpg'
        name = 'KURT'
        member(image, name)

    with cols[2]:
        image = 'franco.jpg'
        name = 'FRANCO'
        member(image, name)

    with cols[3]: 
        image = 'marvin.png'
        name = 'MARVIN'
        member(image, name)

if __name__ =="__main__":
    main()