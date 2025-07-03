from pocketflow import Flow
from nodes import (
    AnswerNode, GetQuestionNode, InputGatherNode, RepoAnalyzerNode, BlogContextNode, PersonalPromptNode,
    BlogDraftGeneratorNode, ReviewAndEditNode, PRCreatorNode
)

def create_qa_flow():
    """Create and return a question-answering flow."""
    # Create nodes
    get_question_node = GetQuestionNode()
    answer_node = AnswerNode()
    
    # Connect nodes in sequence
    get_question_node >> answer_node
    
    # Create flow starting with input node
    return Flow(start=get_question_node)

def create_blog_flow():
    input_node = InputGatherNode()
    repo_node = RepoAnalyzerNode()
    blog_ctx_node = BlogContextNode()
    personal_node = PersonalPromptNode()
    draft_node = BlogDraftGeneratorNode()
    review_node = ReviewAndEditNode()
    pr_node = PRCreatorNode()

    input_node >> repo_node >> blog_ctx_node >> personal_node >> draft_node >> review_node >> pr_node
    return Flow(start=input_node)

qa_flow = create_qa_flow()
blog_flow = create_blog_flow()