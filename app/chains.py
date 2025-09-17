import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

load_dotenv()


class Chain:
    def __init__(self):
        self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.3-70b-versatile")

    def extract_jobs(self, cleaned_text):
        prompt_extract = PromptTemplate.from_template(
        """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            
            The scraped text is from a careers page.
            Extract all job postings and return them as a JSON array.
            Each job posting must contain these keys: 
            - "role": Job title
            - "experience": Required years of experience
            - "skills": List of skills with context
            - "description": Summary of the job, including key responsibilities and requirements
            Only return valid JSON. Do NOT include any explanation, extra text, or commentary.
            If a field is missing in the source, set it to null.
            
            ### VALID JSON (NO PREAMBLE):    

        """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def write_mail(self, job, links):
        prompt_email = PromptTemplate.from_template(
            """
                ### JOB DESCRIPTION:
                {job_description}

                ### INSTRUCTION:
                You are Sravya, applying for the job above. Write a professional, concise, and personalized cold email
                highlighting your skills and experience relevant to the job.
                
                Include the most relevant projects from the following portfolio projects, 
                formatting each as: ProjectName : (Full GitHub URL) : {link_list} 
                each line by line
                
                Also include this portfolio link at the end of the mail: https://example.portfolio.com
                Keep the email within 200–250 words.
                Do not include any preamble, extra text, or commentary.

                ### EMAIL (NO PREAMBLE):
            """
        )

        # Flatten and deduplicate projects by URL
        seen = set()
        unique_links = []
        for sublist in links:
            for proj in sublist:
                if proj["url"] not in seen:  # avoid duplicates
                    seen.add(proj["url"])
                    unique_links.append(proj)
                    
        # Limit to top 4 projects only
        unique_links = unique_links[:4]

        # Format top projects as "ProjectName : 'URL'"
        link_list_str = "\n".join([f"{proj['project_name']}: {proj['url']}" for proj in unique_links])

        # Format job_description nicely
        job_description = (
            f"Role: {job['role']}\n"
            f"Skills: {', '.join(job['skills'])}\n"
            f"Description: {job['description']}"
        )

        # Chain and invoke
        chain_email = prompt_email | self.llm
        res = chain_email.invoke({
            "job_description": job_description,
            "link_list": link_list_str
        })

        
        return res.content

if __name__ == "__main__":
    print(os.getenv("GROQ_API_KEY"))