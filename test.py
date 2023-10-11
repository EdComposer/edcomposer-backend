import picture_gen

inputList = [
{
"generate": True,
"prompt": "An image depicting the rapid militarization of the world's major powers culminating in war."
},
{
"generate": True,
"prompt": "A historically accurate illustration showing the mobilization of more than 100 million military personnel, the largest in history."
},
{
"generate": True,
"prompt": "An abstract representation of significant events involving the mass death of civilians during war."
},
{
"generate": True,
"prompt": "A symbolical artwork representing the Holocaust and the genocide of 6 million Jews."
}
]

output = picture_gen.generatePictures(inputList)
print(output)