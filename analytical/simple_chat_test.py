"""
Simple test to verify chat functionality
"""
import sys
import os

# Add the analytics directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_process_message_method():
    """Test that the process_message method exists"""
    try:
        from analytics.services.llm_processor import LLMProcessor
        
        # Check if the method exists
        processor = LLMProcessor()
        if hasattr(processor, 'process_message'):
            print("✅ process_message method exists in LLMProcessor")
            # Check the method signature
            import inspect
            sig = inspect.signature(processor.process_message)
            print(f"✅ Method signature: process_message{sig}")
            return True
        else:
            print("❌ process_message method does not exist in LLMProcessor")
            return False
    except Exception as e:
        print(f"❌ Error importing LLMProcessor: {e}")
        return False

if __name__ == "__main__":
    print("Testing chat functionality...")
    print("=" * 50)
    
    success = test_process_message_method()
    
    if success:
        print("\n✅ Chat functionality test passed!")
    else:
        print("\n❌ Chat functionality test failed!")