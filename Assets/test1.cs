using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class test1 : MonoBehaviour
{
    public GameObject game;

    // Start is called before the first frame update
    void Start()
    {
        //Destroy(game, 3);

        GameObject inst = Instantiate(game, transform.position, transform.rotation);


        
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
