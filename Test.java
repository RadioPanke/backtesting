/**
 * Definition for singly-linked list.
 */
class ListNode {
     int val;
     ListNode next;
     ListNode() {}
     ListNode(int val) { this.val = val; }
     ListNode(int val, ListNode next) { this.val = val; this.next = next; }
 }
 
class Test {
    public static void main(String []args) {
        System.out.println("hi");
        // System.out.printnl(new Solution().addTwoNumbers())
    }
    
    public ListNode addTwoNumbers(ListNode l1, ListNode l2) {
        int carry = 0;
        ListNode pointer = new ListNode(0, null);
        ListNode resultHead = pointer;

        while(l1 != null || l2 != null || carry != 0) {
            int n1 = l1 != null? l1.val : 0;
            int n2 = l2 != null? l2.val : 0;

            int total = n1 + n2 + carry;
            carry = total % 10;
            pointer.next = new ListNode(total / 10);
            pointer = pointer.next;

            if(l1 != null) {
                l1 = l1.next;
            }
            if(l2 != null) {
                l2 = l2.next;
            }
        }

        return resultHead.next;

    }
}